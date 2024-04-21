from copy import copy
import random
import string
from datetime import datetime
from typing import List, Union

from fastapi import APIRouter, Depends, Response
from fastapi_sqlalchemy import db
from ChainUser.model import ChainUser
from ChainUser.schema import ChainUserSchema
from Party.model import Party


# from src.error.NotFoundException import NotFoundException

router = APIRouter(
    prefix="/party",
)

def get_party(code:str):
    p = db.session.query(Party).filter(Party.ended == False).filter(Party.code == code).first()
    if p is None:
        raise Exception('Party not found')
    return p
def get_party_by_id(id:int):
    p = db.session.query(Party).filter(Party.id == id).first()
    if p is None:
        raise Exception('Party not found')
    return p
def get_party_users(id:int):
    return db.session.query(ChainUser).filter(ChainUser.party_id == id).all()


def get_user(id:int):
    p = db.session.query(ChainUser).filter(ChainUser.id == id).first()
    if p is None:
        raise Exception('Party not found')
    return p
def get_killer(id:int):
    p = db.session.query(ChainUser).filter(ChainUser.next_user_id == id).first()
    if p is None:
        raise Exception('Party not found')
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
        except Exception:
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

@router.put("/{code}/start/{user_id}")
def start(code:str, user_id:int):
    p = get_party(code)
    if not p.creator_id == user_id:
        raise Exception('Not autorized')
    if p.started:
        raise Exception('Party already started')
    # ul=copy.deepcopy(p.users)
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

@router.post("/{code}/join/")
def join(code:str, user:ChainUserSchema):
    p = get_party(code)
    u = create_user(user, p.id)
    return {
            'name': u.name,
            'code': code,
            'user_id': u.id,
            'users': [{'name': u.name, 'image': u.image} for u in get_party_users(p.id)]
        }


@router.put("/{code}/{user_id}/die")
def die(party:str,user_id:int):
    u = get_user(user_id)
    p = get_party(party)
    if u.dead:
        raise Exception()
    k = get_killer(user_id)
    if k.dead:
        raise Exception()
    u.dead = True
    k.next_user_id = u.next_user_id
    if k.next_user_id == k.id:
       p.ended = True
       p.winner_id = k.id 
    u.next_user_id = None
    db.session.commit()
    db.session.refresh(u)
    db.session.refresh(k)

@router.get("/{user_id}/refresh")
def refresh(user_id:int):
    u = get_user(user_id)
    p = get_party_by_id(u.party_id)
    
    if p.ended:
        w = get_user(p.winner_id)
        return {
            'winner': {
                'winner_name': w.name,
                'winner_image': w.image
            },
            'remaining_users': len([u for u in get_party_users(p.id) if not u.dead]),
        }
    if p.started:
        if u.dead:
            return {
                'name': u.name,
                'image': u.image,
                'dead': u.dead,
                'remaining_users': len([u for u in get_party_users(p.id) if not u.dead]),
            }
        t = get_user(u.next_user_id)

        return {
                'name': u.name,
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
        'users': [{'name': u.name, 'image': u.image} for u in get_party_users(p.id)]
    }
