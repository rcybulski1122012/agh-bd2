# System zarządzania biblioteką


## Skład Grupy
- Radosław Cybulski rcybulski@student.agh.edu.pl
- Jakub Chrzanowski jchrzanowski@student.agh.edu.pl


## Technologie
- Python
- MongoDB
- Flask (Jinja)
- Bunnet (ODM) & Pydantic
- Bootstrap 5


## Uruchamianie
- Utwórz i aktywuj wirtualne środowisko
    ```bash
    python -m venv venv
    source venv/bin/activate  # na systemie Linux lub MacOS
    venv\Scripts\activate     # na systemie Windows
    ```
- Zainstaluj potrzebne pakiety 
    ```bash 
    pip install -r requirements.txt
    ```
- Ustaw zmienną środowiskową `MONGO_URI` (serwer powinien zostać uruchomiony wraz z `Replica Set`)
- Uruchom serwer aplikacji
    ```bash
    python -m app 
    ```
- Dodatkowo można skorzysać ze skryptu generującego losowe dane
  ```bash
    python -m populate_db
  ```


## Mapowanie Danych
Do mapowania danych na obiekty Pythona została wykorzystana bibloteka ODM (Object Document Mapper) o nazwie `Bunnet`.
Pozwoliło to ograniczyć ilość kodu potrzebnego do obsługi bazy danych (m. in. tworzenie indeksów)
oraz uprościło proces tworzenia zapytań.
Dodatkowo oparta jest ona na bibliotece `Pydantic` co pozwala na walidację danych przychodzących do aplikacji.


## Modele


### Book
Model `Book` reprezentuje książkę, zawierając takie pola jak tytuł, autorzy, wydawca i numer ISBN.
W modelu zastosowano indeksy dla czterech pól: `title`, `publication_date`, `isbn` oraz `genre`
co przyspiesza przeszukiwanie i sortowanie w bazie danych.

Model zawiera również dwa pola związane z recenzjami: review_count (ilość recenzji) i avg_rating (średnia ocena).
Zastosowano tutaj denormalizacje, aby nie musieć wykonywać dodatkowego zapytania do bazy danych
przy każdym wyświetleniu książki.

Do każdego modelu potrzebe było dodnie klasy Setting, gdyż biblioteka `Bunnet` nie obsługiwała denormalizacji
do formatu BSON Python'owych typów `datetime` oraz `date`. Dodatkowo zawiera ona kilka pomocniczych metod,
które zostały pominięte dla czytelności dokumentacji.


```python
class Book(Document):
    title: Indexed(str)
    authors: list[str]
    topic: str
    genre: Indexed(str)  # BookGenre
    publication_date: Indexed(datetime.date)
    description: str
    publisher: str
    isbn: Indexed(str)
    pages: int
    stock: int
    initial_stock: int
    review_count: int = 0
    avg_rating: Decimal = Decimal(0)
    images_urls: list[str]
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    class Settings:
        bson_encoders = {**datetime_encoders}

    ...
```

### User

Model `User` reprezentuje użytkownika, zawierając takie pola jak imię, nazwisko, adres email, numer telefonu oraz dodatkowe informacje, takie jak czy użytkownik jest administratorem.
W modelu zastosowano indeksy dla czterech pól: `first_name`, `last_name`, `email` oraz `phone_number`.

Dodatkowo, pole `email` ma atrybut `unique=True` zapewniający, że dany adres email może być przypisany tylko do jednego użytkownika. Podobnie dla pola `phone_number`, które również jest unikalne.

Klasa ta dziedziczy po klasie `UserMixin` z biblioteki `flask_login`, która implementuje domyślne metody wymagane
przez tę bibliotekę.

```python
class User(UserMixin, Document):
    first_name: Indexed(str)
    last_name: Indexed(str)
    email: Indexed(str, unique=True)
    phone_number: Indexed(str, unique=True)
    password: str
    address: Address
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    updated_at: Optional[datetime.datetime] = None
    is_admin: bool = False
    
    ...
```

### Rent

Model `Rent` reprezentuje wypożyczenie książki przez użytkownika.
Główne pola to book oraz user, które odnoszą się do odpowiednich dokumentów Book i User za pomocą struktury Link.
Zastosowanie tej struktury pozwala na automatyczne pobranie dokumentu stosując flagę `fetch_links`.
W bazie danych przechowywane są jedynie referencje do dokumentów (`id` oraz nazwa kolekcji)


```python
class Rent(Document):
    book: Link[Book]
    user: Link[User]
    rent_date: datetime.date = Field(default_factory=datetime.date.today)
    due_date: datetime.date = Field(default_factory=next_month_factory)
    return_date: Optional[datetime.date] = None

    class Settings:
        bson_encoders = {**datetime_encoders}
    
    ...
```

### Review

Model `Review` reprezentuje recenzję książki przez użytkownika, zawierając takie pola jak
`book_id`, `user`, `rating`, czy `comment`.

Podobnie jak w modelu `Rent`, pole `user` odnosi się do dokumentu
za pomocą struktury `Link`. Natomiast nie zastosowano tego dla relacji z `Book`, gdyż nie było to przydatne w
żadnym zapytaniu. 

Typ `PydanticObjectId` jest typem pomocniczym, który pozwala na serializację obiektów typu `ObjectId` (reprezentujacych wbudowane id z MongoDB) z biblioteki `bson` i jest zapewniony przez ODM.


```python
class Review(Document):
    book_id: Indexed(PydanticObjectId)
    user: Link[User]
    rating: int
    comment: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    ...
```

### Address

Model `Address` nie dziedziczy po klasie `Document`, a po klasie `BaseModel`(`Pydantic`) gdyż nie jest
on elementem kolekcji, a dokumentem osadzonym w innych dokumentach.

```python
class Address(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str
    
    ...
```

## Walidacja danych i formularze

Walidacja danych w aplikacji jest realizowana zarówno na poziomie modeli, jak i formularzy.
Modele bazują na klasie Pydantic BaseModel, co gwarantuje walidację atrybutów zgodnie z zdefiniowanymi
typami. Zastosowano również formularze z pakietu Flask-WTF, które pozwalają na klienta odwalidować
dane przed przesłaniem ich do serwera.

Przykładowy formularz do rejestracji użytkownika

```python
class RegisterForm(FlaskForm):
    first_name = StringField(
        "First name",
        validators=[DataRequired(), Length(max=100, message="First name too long")],
    )
    last_name = StringField(
        "Last name", validators=[DataRequired(), Length(max=100, message="Last name too long")]
    )
    email = EmailField("Email", validators=[DataRequired(), Email(message="Invalid email")])
    phone_number = StringField(
        "Phone number",
        validators=[DataRequired(), Length(max=100, message="Phone number too long")],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password")]
    )

    street = StringField(
        "Street", validators=[DataRequired(), Length(max=100, message="Street too long")]
    )
    city = StringField(
        "City", validators=[DataRequired(), Length(max=100, message="City too long")]
    )
    postal_code = StringField(
        "Postal code",
        validators=[DataRequired(), Length(max=100, message="Postal code too long")],
    )
    country = StringField(
        "Country", validators=[DataRequired(), Length(max=100, message="Country too long")]
    )
    submit = SubmitField("Sign Up")

    def validate_email(self, email):
        user = User.find_one(User.email == email.data).run()

        if user:
            raise ValidationError("This email is taken.")

    def validate_phone_number(self, phone_number):
        user = User.find_one(User.phone_number == phone_number.data).run()

        if user:
            raise ValidationError("This phone number is taken.")
```

Łatwo mogliśmy rozszerzyć ten formularz o walidację unikalności numeru telefonu czy adresu email,
nadpisując metody `validate_email` oraz `validate_phone_number`. 

Zastosowanie prostego marka silnika szablonów pozwoliło łatwo prezentowa pola formularza:

```html
{% macro render_field(form, field_name, label_class='form-control-label', input_class='form-control form-control-lg') %}
  <div class="form-group">
    {{ form[field_name].label(class=label_class) }}
    {% if form[field_name].errors %}
    {{ form[field_name](class=input_class ~ ' is-invalid') }}
    <div class="invalid-feedback">
      {% for error in form[field_name].errors %}
      <span>{{ error }}</span>
      {% endfor %}
    </div>
    {% else %}
    {{ form[field_name](class=input_class) }}
    {% endif %}
  </div>
{% endmacro %}
```

## Autentykacja i autoryzacja

Autentykacja i autoryzacja użytkowników jest realizowana za pomocą biblioteki Flask-Login.
Poza użyciem wspomnainej klasy domieszki `UserMixin` potrzebne było "zarejestrowanie" modelu urzytkownika.

```python
@login_manager.user_loader
def load_user(user_id: str):
    return User.get(PydanticObjectId(user_id)).run()
```

Widoki wymagające zalogowania użytkownika są zabezpieczone za pomocą dekoratora `@login_required`.

```python
@books.route("/books", methods=["GET"])
@login_required
def list_books():
    ...
```

Dodatkowo, aby zabezpieczyć niektóre widoki przed nieautoryzowanym dostępem, zastosowano dekorator `@admin_role_required`.

```python
def admin_role_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            raise abort(403)
        return func(*args, **kwargs)

    return wrapper
```


## Główne funkcjonalności

### Lista książek

Każdy zalogowany użytkownik ma dostęp do paginowanej listy książek.
Ksiązki można filtrować po tytule, autorze, gatunku, dostępności oraz ISBN.
Możliwe jest również sortowanie po tytule liczbie stron lub dacie publikacji.

```python
@books.route("/books", methods=["GET"])
@login_required
def list_books():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 24, type=int)

    filters = {
        "title": request.args.get("title", None),
        "genre": request.args.get("genre", None),
        "author": request.args.get("author", None),
        "available": request.args.get("available", None, type=bool),
        "isbn": request.args.get("isbn", None),
        "order_by": request.args.get("order_by", None),
    }
    form = FilterBooksForm(**filters)
    filters_query_string = "&".join([f"{k}={v}" for k, v in filters.items() if v])

    query = Book.filter(**filters)
    books_ = query.skip((page - 1) * page_size).limit(page_size).run()
    total = query.count()

    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size),
    }

    return render_template(
        "books/list_books.html",
        form=form,
        books=books_,
        pagination=pagination,
        filters_query_string=filters_query_string,
    )
```

Do pobierania danych przygotowano pomocniczą metodę klasową `Book.fliter`,
która opdowiada za filtrowanie i sortowanie książek na podstawie podanych filtów, korzystając z metod
zapewnionych przez bibliotekę `Bunnet` i klasę `Document`.

```python
@classmethod
def filter(
    cls,
    title: str = None,
    genre: BookGenre = None,
    author: str = None,
    available: bool = None,
    isbn: str = None,
    order_by: str = None,
):
    query = cls.find()

    if title:
        query = query.find(
            RegEx(cls.title, f".*{title}.*", "i"),
        )

    if genre:
        query.find(
            cls.genre == genre,
        )

    if author:
        query.find(
            ElemMatch(cls.authors, {"$regex": author, "$options": "i"}),
        )

    if available:
        query.find(
            cls.stock > 0,
        )

    if isbn:
        query.find(
            RegEx(cls.title, f".*{title}.*", "i"),
        )

    if order_by and order_by != BookOrders.NONE:
        if order_by == BookOrders.TITLE_ASC:
            query = query.sort(cls.title)
        elif order_by == BookOrders.TITLE_DSC:
            query = query.sort(-cls.title)
        elif order_by == BookOrders.PAGES_ASC:
            query = query.sort(cls.pages)
        elif order_by == BookOrders.PAGES_DSC:
            query = query.sort(-cls.pages)
        elif order_by == BookOrders.PUB_DATE_ASC:
            query = query.sort(cls.publication_date)
        elif order_by == BookOrders.PUB_DATE_DSC:
            query = query.sort(-cls.publication_date)

    return query
```

Paginację zaimplementowano poprzez wykorzystanie wbudowanych metod `skip` i `limit`;
potrzebne było wykonanie dodatkowego zapytania w celu obliczenia liczby obiektów (`.count()`).
Do wyświetlania paginacji zastosowano makro `render_pagination`. Podobne podejście zastosowano w liście członków.

```html
{% macro render_pagination(pagination, url, filters_query_string) %}
{% if pagination.total != 0 %}
<nav aria-label="Page navigation" class="mt-3">
    <ul class="pagination justify-content-center">
        <li class="page-item {% if pagination.page == 1 %}disabled{% endif %}">
            <a class="page-link" href="{{ url }}?page=1&page_size={{ pagination.page_size }}&{{ filters_query_string }}" aria-label="First">
                <span aria-hidden="true">&laquo;</span>
                <span class="visually-hidden">First</span>
            </a>
        </li>
        <li class="page-item {% if pagination.page == 1 %}disabled{% endif %}">
            <a class="page-link" href="{{ url }}?page={{pagination.page - 1}}&page_size={{ pagination.page_size }}&{{ filters_query_string }}" aria-label="Previous">
                <span aria-hidden="true">&lsaquo;</span>
                <span class="visually-hidden">Previous</span>
            </a>
        </li>
        {% for i in range(pagination.page - 2, pagination.page + 3) %}
            {% if i > 0 and i <= pagination.total_pages %}
                <li class="page-item {% if pagination.page == i %}active{% endif %}"><a class="page-link" href="{{ url }}?page={{ i }}&page_size={{ pagination.page_size }}&{{ filters_query_string }}">{{ i }}</a></li>
            {% endif %}
        {% endfor %}
        <li class="page-item {% if pagination.page == pagination.total_pages %}disabled{% endif %}">
            <a class="page-link" href="{{ url }}?page={{ pagination.page + 1}}&page_size={{ pagination.page_size }}&{{ filters_query_string }}" aria-label="Next">
                <span aria-hidden="true">&rsaquo;</span>
                <span class="visually-hidden">Next</span>
            </a>
        </li>
        <li class="page-item {% if pagination.page == pagination.total_pages %}disabled{% endif %}">
            <a class="page-link" href="{{ url }}?page={{ pagination.total_pages }}&page_size={{ pagination.page_size }}&{{ filters_query_string }}" aria-label="Last">
                <span aria-hidden="true">&raquo;</span>
                <span class="visually-hidden">Last</span>
            </a>
        </li>
    </ul>
</nav>
{% endif %}
{% endmacro %}
```


### Detale książek

Widok `book_detail` wyświetla szczegóły książki, jej recenzje oraz formularz do wypożyczenia książki.

```python
@books.route("/books/<book_id>", methods=["GET", "POST"])
@login_required
def book_detail(book_id):
    book = Book.get(book_id).run()
    reviews = Review.find(Review.book_id == PydanticObjectId(book_id), fetch_links=True).run()

    already_rented = bool(
        Rent.find_one(
            Rent.book.id == PydanticObjectId(book_id),
            Rent.user.id == PydanticObjectId(current_user.id),
        ).run()
    )

    review_added = bool(
        Review.find_one(
            Review.book_id == PydanticObjectId(book_id),
            Review.user.id == PydanticObjectId(current_user.id),
        ).run()
    )

    form = RentBookForm()
    if request.method == "POST":
        if not current_user.is_admin:
            abort(403)

        user = (
            User.find_one({"email": form.email_or_phone_number.data}).run()
            or User.find_one({"email": form.email_or_phone_number.data}).run()
        )

        if not user:
            flash("User not found", "danger")
            return redirect(url_for("books.book_detail", book_id=book_id))

        return redirect(url_for("books.rent_book", book_id=book_id, user_id=str(user.id)))

    return render_template(
        "books/book_detail.html",
        book=book,
        form=form,
        reviews=reviews,
        already_rented=already_rented,
        review_added=review_added,
    )
```

### Wypożyczanie książek

Widok `rent_book` jest dostępny tylko dla administratorów. Pozwala on na
wypożyczenie książki użytkownikowi o podanym adresie email lub numerze telefonu.
Operacje w tym przypadku są wykowonywane transakcyjnie. Bibliotego `Bunnet` póki co
nie wspera transakcji, dlatego wykorzystano bezpośrednio bibliotekę `pymongo`.

```python

```python
@books.route("/books/<book_id>/rent/<user_id>", methods=["GET"])
@login_required
@admin_role_required
def rent_book(book_id, user_id):
    user = User.get(user_id).run()
    book = Book.get(book_id).run()
    rent = Rent.find_one(
        Rent.book.id == PydanticObjectId(book_id),
        Rent.user.id == PydanticObjectId(user_id),
        Rent.return_date == None,  # noqa
    ).run()

    if not book or not user:
        raise abort(404)

    if rent:
        flash("Book already rented", "danger")
        return redirect(book.detail_url)

    if not book.is_available:
        raise abort(403)

    with mongo_client.start_session() as session, session.start_transaction():
        book.stock -= 1
        book.save(session=session)
        rent = Rent(book=book, user=user)
        rent.save(session=session)

    flash("Book rented successfully", "success")
    return redirect(url_for("auth.user_details", user_id=user_id))
```

### Zwracanie książek

Widok `return_book` pozwala na zwracanie książek i jest dostępny tylko dla
administratora. Podobnie jak w `rent_book` wykożystaliśmy mechanizm transakcji.

```python
@books.route("/books/<book_id>/return/<user_id>", methods=["GET"])
@login_required
@admin_role_required
def return_book(book_id, user_id):
    rent = Rent.find_one(
        Rent.book.id == PydanticObjectId(book_id),
        Rent.user.id == PydanticObjectId(user_id),
        Rent.return_date == None,  # noqa
    ).run()

    if not rent:
        raise abort(404)

    with mongo_client.start_session() as session, session.start_transaction():
        book = Book.get(book_id).run()
        book.stock += 1
        book.save(session=session)
        rent.return_date = datetime.date.today().isoformat()
        rent.save(session=session)

    flash("Book returned successfully", "success")
    return redirect(url_for("auth.user_details", user_id=user_id))
```


### Usuwanie ksiązek

```python
@books.route("/books/remove/<book_id>", methods=["GET"])
@login_required
@admin_role_required
def remove_book(book_id):
    try:
        book = Book.get(book_id).run()
        book.delete()
        flash("Book has been removed", "success")
    except Exception:
        flash("Removing error", "error")

    return redirect(url_for("books.list_books"))
```


### Dodawanie książek

```python
@books.route("/books/add_book", methods=["GET", "POST"])
@login_required
@admin_role_required
def add_book():
    form = AddBookForm()
    if request.method == "POST" and form.validate_on_submit():
        book = Book(
            title=form.title.data,
            authors=form.authors.data.split(","),
            topic=form.topic.data,
            genre=form.genre.data,
            publication_date=form.publication_date.data,
            publisher=form.publisher.data,
            description=form.description.data,
            isbn=form.isbn.data,
            pages=form.pages.data,
            stock=form.stock.data,
            initial_stock=form.stock.data,
            images_urls=[faker.image_url() for _ in range(random.randint(1, 3))],
        )
        book.authors = book.authors[0].split(",")
        book.save()
        flash("New book has been added", "success")
        return redirect(url_for("books.list_books"))

    return render_template("books/add_book.html", form=form)
```


### Zaległe zwroty

Widok `overdue_returns` zwraca paginowaną listę zaległych zwrotów posortowaną po terminie zwrotu.
Dostępny jest tylko dla administratora.

```python
@books.route("/returns/overdue", methods=["GET"])
@login_required
@admin_role_required
def overdue_returns():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 24, type=int)

    query = Rent.get_overdue().find(fetch_links=True).sort(Rent.due_date)
    rents = query.skip((page - 1) * page_size).limit(page_size).run()
    total = query.count()

    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size),
    }

    return render_template("books/overdue_returns.html", rents=rents, pagination=pagination)
```


### Dodawanie recenzji

Widok `add_review` pozwala na dodawanie recenzji do książek.
Dostępny jest tylko dla użytkowników, któży wypożyczyli daną książkę.
Podobnie jak w powyżych widokach zastosowano mechanizm transakcji

```python
@books.route("/books/<book_id>/add_review", methods=["GET", "POST"])
def add_review(book_id):
    book = Book.get(book_id).run()

    review = Review.find_one(
        Review.book_id == PydanticObjectId(book_id),
        Review.user.id == PydanticObjectId(current_user.id),
    ).run()

    rent = Rent.find_one(
        Review.book_id == PydanticObjectId(book_id),
        Review.user.id == PydanticObjectId(current_user.id),
    )

    if not book:
        abort(404)

    if review:
        abort(403)

    if not rent:
        abort(403)

    form = AddReviewForm()
    if request.method == "POST" and form.validate_on_submit():
        rating = Decimal(form.rating.data)
        with mongo_client.start_session() as session, session.start_transaction():
            review = Review(
                book_id=book_id,
                user=current_user,
                rating=rating,
                comment=form.comment.data,
            )
            book.add_review(rating)
            book.save(session=session)
            review.save(session=session)

        flash("New review has been added", "success")
        return redirect(url_for("books.book_detail", book_id=book_id))

    return render_template("books/add_review.html", form=form, book=book)
```

Nowe wartości dla `avg_rating` są obliczane w metodize pomocnicznej:

```python
def add_review(self, rating: int):
    self.avg_rating = (self.avg_rating * self.review_count + rating) / (
        self.review_count + 1
    )
    self.review_count += 1
```

### Lista członków

Widok `member_list` zwraca paginowaną paginowaną listę użytkowników.
Sortowanie, filtrowanie i paginacja zostały zaimplementowane analogicznie
do widoku `book_list`.

```python
@auth.route("/members", methods=["GET"])
@login_required
@admin_role_required
def member_list():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 24, type=int)

    filters = {
        "first_name": request.args.get("first_name", None),
        "last_name": request.args.get("last_name", None),
        "email": request.args.get("email", None),
        "phone_number": request.args.get("phone_number", None),
    }

    form = SearchUserForm(**filters)
    filters_query_string = "&".join([f"{k}={v}" for k, v in filters.items() if v])

    query = User.filter(**filters)
    users = query.skip((page - 1) * page_size).limit(page_size).run()
    total = query.count()

    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": math.ceil(total / page_size),
    }

    return render_template(
        "auth/member_list.html",
        form=form,
        users=users,
        pagination=pagination,
        filters_query_string=filters_query_string,
    )
```

### Delate użytkownika

```python
@auth.route("/members/<user_id>", methods=["GET"])
@login_required
def user_details(user_id):
    user = User.get(user_id).run()

    if not current_user.is_admin and current_user.id != user.id:
        abort(403)

    if not user:
        abort(404)

    rents = (
        Rent.find(Rent.user.id == PydanticObjectId(user_id), fetch_links=True)
        .sort(-Rent.rent_date)
        .run()
    )
    already_returned = [rent for rent in rents if rent.return_date]
    not_returned = [rent for rent in rents if not rent.return_date]

    return render_template(
        "auth/user_details.html",
        user=user,
        already_returned=already_returned,
        not_returned=not_returned,
    )
```

### Rejestracja użytkownika

Widok `register` pozwala na rejestrację nowego użytkownika.
Skorzystano z biblotegi `bcrypt` do hashowania hasła.
Domyślnie każdy użyktownik ma flagę `is_admin` ustawioną na `False`.
Jedynym sposobem na zmianę roli jest zrobienie tego ręcznie w bazie danych.

```python
@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            password=hashed_password,
            address=Address(
                street=form.street.data,
                city=form.city.data,
                postal_code=form.postal_code.data,
                country=form.country.data,
            ),
        )
        user.insert()
        flash("Your account has been created! You are now able to log in", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)
```

### Logowanie i wylogowywanie użytkownika

```python
@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        user = User.find_one(User.email == form.email.data).run()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get("next")
            flash("You have been logged in!", "success")
            return redirect(next_page) if next_page else redirect(url_for("main.home"))
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")
    return render_template("auth/login.html", form=form)
```

```python
@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.home"))
```

### Modyfikacja książek

```python
@books.route("/books/modify/<book_id>", methods=["GET", "POST"])
@login_required
@admin_role_required
def modify_book(book_id):
    form = ModifyBookForm(book_id)
    if request.method == "POST" and form.validate_on_submit():
        book = Book.get(book_id).run()
        book.title = form.title.data
        book.authors=form.authors.data.split(",")
        book.topic=form.topic.data
        book.genre=form.genre.data
        book.publication_date=form.publication_date.data
        book.publisher=form.publisher.data
        book.description=form.description.data
        book.isbn=form.isbn.data
        book.pages=form.pages.data
        book.stock=form.stock.data
        book.initial_stock=form.stock.data
        book.images_urls=[faker.image_url() for _ in range(random.randint(1, 3))]

        book.authors = book.authors[0].split(",")
        book.save()
        flash("Book has been modified", "success")
        return redirect(url_for("books.list_books"))
    
    return render_template("books/add_book.html", form=form)
```
