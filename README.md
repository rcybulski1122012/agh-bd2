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


## Głowne funkcjonalności

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
