from Base.BaseSchema import BaseSchema


class ChainUserSchema(BaseSchema):
    name: str
    image: str

class ChainUserInput(BaseSchema):
    id: int