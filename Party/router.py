import random
import string
from fastapi import APIRouter
from fastapi_sqlalchemy import db
from ChainUser.model import ChainUser
from ChainUser.schema import ChainUserSchema, ChainUserInput
from Configuration import Configuration
from Party.model import Party
from error.InvalidDataException import InvalidDataException


router = APIRouter( 
    prefix="/party",
)

def get_party(code:str):
    p = db.session.query(Party).filter(Party.ended == False).filter(Party.code == code).first()
    if p is None:
        raise InvalidDataException('Party not found')
    return p

def get_party_by_id(id:int):
    p = db.session.query(Party).filter(Party.id == id).first()
    if p is None:
        raise InvalidDataException('Party not found')
    return p

def get_party_by_user(user_id:int):
    u = db.session.query(ChainUser).filter(ChainUser.id == user_id).first()
    if u is None:
        raise InvalidDataException('User not found')
    return get_party_by_id(u.party_id)

def get_party_users(id:int):
    return db.session.query(ChainUser).filter(ChainUser.party_id == id).all()

def get_user(id:int):
    p = db.session.query(ChainUser).filter(ChainUser.id == id).first()
    if p is None:
        raise InvalidDataException('User not found')
    return p

def get_killer(id:int):
    p = db.session.query(ChainUser).filter(ChainUser.next_user_id == id).first()
    if p is None:
        raise InvalidDataException('Killer not found')
    return p

def create_user(user:ChainUserSchema, party_id:int):
    u = ChainUser(**user.dict(), party_id = party_id)
    db.session.add(u)
    db.session.commit()
    db.session.refresh(u)
    return u

def generate_code(num_dig=4):
    code = ''
    while(True):
        code = ''.join(random.choices(string.ascii_uppercase, k=num_dig))
        try:
            get_party(code)
        except InvalidDataException:
            return code
        
@router.post("/create")
def create(user:ChainUserSchema):
    party = Party(code= generate_code())
    db.session.add(party)
    db.session.commit()
    db.session.refresh(party)
    u = create_user(user,party_id=party.id)
    party.creator_id = u.id
    db.session.commit()
    db.session.refresh(party)
    return {'party':{
                'id': party.id,
                'code': party.code},
            'user':u.id}

@router.put("/start/{user_id}")
def start(user_id:int):
    u = get_user(user_id)
    p = get_party_by_id(u.party_id)
    if not p.creator_id == user_id:
        raise InvalidDataException('Not autorized')
    if p.started:
        raise InvalidDataException('Party already started')
    if p.ended:
        raise InvalidDataException('Party already ended')
    if len(get_party_users(p.id))<3:
        raise InvalidDataException('Min users playing is 3')
    ul=get_party_users(p.id)
    random.shuffle(ul)
    for i in range(len(ul)):
        ul[i].next_user_id = ul[(i+1)%len(ul)].id
    p.started = True
    db.session.commit()
    db.session.refresh(p)
    for u in ul:
        db.session.refresh(u)
    return p.code

@router.post("/{code}/join")
def join(code:str, user:ChainUserSchema):
    p = get_party(code)
    existing_player = db.session.query(ChainUser).filter(ChainUser.name == user, p == ChainUser.party_id)
    if existing_player:
        raise InvalidDataException("There is already one player with this name")
    u = create_user(user, p.id)
    return {
            'name': u.name,
            'code': code,
            'user_id': u.id,
            'users': [{'name': u.name, 'image': u.image} for u in get_party_users(p.id)]
        }

@router.put("/{user_id}/die")
def die(user_id:int):
    u = get_user(user_id)
    p = get_party_by_id(u.party_id)
    if p.ended:
        raise InvalidDataException('Party already ended')
    if not p.started:
        raise InvalidDataException('Party not started')
    if u.dead:
        raise InvalidDataException()
    k = get_killer(user_id)
    if k.dead:
        raise InvalidDataException()
    u.dead = True
    k.num_killed += 1
    k.next_user_id = u.next_user_id
    if k.next_user_id == k.id:
       p.ended = True
       p.winner_id = k.id 
    u.next_user_id = None
    db.session.commit()
    db.session.refresh(u)
    db.session.refresh(k)

@router.get("/{code}/remaining")
def get_remaining(code:str):
    party = get_party(code)
    return get_party_users(party.id)

@router.get("/{code}/exist")
def exist(code:str):
    try:
        get_party(code)
        return True
    except:
        return False
    
@router.delete('/reset/{secret}')
def reset(secret:str):
    if secret != Configuration.secret:
        raise InvalidDataException('Secret not correct')
    db.session.query(Party).delete()
    db.session.query(ChainUser).delete()
    db.session.commit()

@router.delete("/{user_id}")
def delete(user_id:int, payload:ChainUserInput):
    p = get_party_by_user(user_id)
    if user_id == p.creator_id:
        raise InvalidDataException('Leader can not be removed from the party')
    if payload.id != p.creator_id:
        raise InvalidDataException('Only party leader can remove players')
    u = get_user(user_id)
    db.session.delete(u)
    db.session.commit()
    return u
    

@router.get("/{user_id}/refresh")
def refresh(user_id:int):
    u = get_user(user_id)
    p = get_party_by_id(u.party_id)
    if p.ended:
        w = get_user(p.winner_id)
        return {
            'winner': {
                'id': w.id,
                'name': w.name,
                'image': w.image,
                'num_killed': w.num_killed
            },
            'num_killed': u.num_killed,
            'total_users': len(get_party_users(p.id)),
            'remaining_users': len([u for u in get_party_users(p.id) if not u.dead]),
        }
    if p.started:
        if u.dead:
            return {
                'name': u.name,
                'image': u.image,
                'dead': u.dead,
                'num_killed': u.num_killed,
                'total_users': len(get_party_users(p.id)),
                'remaining_users': len([u for u in get_party_users(p.id) if not u.dead]),
            }
        t = get_user(u.next_user_id)
        return {
                'name': u.name,
                'num_killed': u.num_killed,
                'total_users': len(get_party_users(p.id)),
                'remaining_users': len([u for u in get_party_users(p.id) if not u.dead]),
                'target': {
                        'name': t.name,
                        'image': t.image
                    }
            }
    return {
        'name': u.name,
        'code': p.code,
        'is_creator': p.creator_id == user_id,
        'users': [{ 'id': u.id, 'name': u.name, 'image': u.image} for u in get_party_users(p.id)]
    }
