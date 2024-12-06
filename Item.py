class Item:
    def __init__(self, name: str, price: str):
        self.name = name
        self.price = price

    def __eq__(self, other):
        return self.name == other.name and self.name == other.name
