from faker import Faker
fake = Faker()

def name(data):
    fake_name = fake.name().split()
    data.firstname = fake_name[0]
    data.lastname = fake_name[1]
    return data