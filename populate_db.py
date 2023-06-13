import random

from faker import Faker

from library import create_app
from library.auth.models import User
from library.books.models import Book
from library.books.models import BookGenre
from library.books.models import Rent

faker = Faker()


def generate_isbn():
    return f"{random.randint(1000000000, 9999999999)}"


def generate_sample_addresses():
    return {
        "street": faker.street_address(),
        "city": faker.city(),
        "postal_code": faker.postcode(),
        "country": faker.country(),
    }


def populate_db():
    users = []
    for _ in range(100):
        user = User(
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            email=faker.email(),
            phone_number=faker.phone_number(),
            password=faker.password(),
            address=generate_sample_addresses(),
            is_admin=faker.boolean(20),
        )
        users.append(user)

    user_ids = User.insert_many(users).inserted_ids  # type: ignore

    books = []
    for _ in range(1000):
        stock = faker.random_int(1, 50)
        book = Book(
            title=faker.sentence(),
            authors=[faker.name() for _ in range(random.randint(1, 2))],
            topic=faker.word(),
            genre=random.choice(list(BookGenre)).value,
            publication_date=faker.date_between(start_date="-30y", end_date="today"),
            publisher=faker.company(),
            description=faker.text(),
            isbn=generate_isbn(),
            pages=faker.random_int(100, 1000),
            stock=stock,
            initial_stock=stock + 5,
            images_urls=[faker.image_url() for _ in range(random.randint(1, 3))],
            created_at=faker.date_time_this_year(),
            updated_at=faker.date_time_this_year(),
        )
        books.append(book)

    books_ids = Book.insert_many(books).inserted_ids  # type: ignore

    rents = []
    for _ in range(500):
        i = random.randint(0, len(books_ids) - 1)
        book = books[i]
        book_id = books_ids[i]
        book.id = book_id
        j = random.randint(0, len(user_ids) - 1)
        user = users[j]
        user_id = user_ids[j]
        user.id = user_id
        rent = Rent(
            book=book,
            user=user,
            rent_date=faker.date_between(start_date="-2m", end_date="today"),
            due_date=faker.date_between(start_date="-5d", end_date="+15d"),
            return_date=faker.date_between(start_date="-2d", end_date="+12d")
            if faker.boolean(70)
            else None,
        )
        rents.append(rent)

    Rent.insert_many(rents)  # type: ignore


if __name__ == "__main__":
    create_app()
    populate_db()
