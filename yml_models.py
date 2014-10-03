#! /usr/bin/python
# -*- coding: utf8 -*-
""" объекты для работы с БД """

# from sqlalchemy import *
# from sqlalchemy.orm import create_session, relationship
# from sqlalchemy.orm.mapper import Mapper
# from sqlalchemy.orm import mapper
# from sqlalchemy import Column
# from sqlalchemy.ext.declarative import declarative_base


from sqlalchemy import Column, Integer, Unicode, String, Float
from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session

Base = declarative_base()

class Goods( Base ):
    """ Товары """
    __tablename__ = 't_goods'
    id=Column( Integer, primary_key=True)
    name=Column( Unicode)
    alias=  Column( Unicode)
    brand=Column( Unicode)
    model_name=Column( Unicode)
    full_name=Column( Unicode)
    section_guid=Column( Unicode, ForeignKey('t_goods_sections.guid') )
    block_id=Column( Integer, ForeignKey('t_goods_block.id') )
    overall_type=Column( Integer)
    logic_weight = Column( DECIMAL )
    description = Column(Unicode)
    prop_full = Column(Unicode)

class Rates( Base ):
    """ Стоимость доставки в ДПД регионы """
    __tablename__ = 't_region_city_rates'
    max_weight = Column( Integer )
    city_id = Column( Integer, primary_key=True )
    cost = Column( Float )

class Region( Base ):
    """ Регионы """
    __tablename__="t_cities"#, metadata,
    id=Column(Integer, primary_key=True)
    name=Column( Unicode)
    domain=Column( Unicode)
    price_type_guid=Column( String())
    delivery_default=Column( String() )

class Shops( Base ):
    """Магазины региона"""
    __tablename__="t_shops"#, metadata,
    id=Column(Integer, primary_key=True)
    city_id=Column(Integer, ForeignKey('t_cities.id'))
    flag_no_self_delivery_kbt = Column( Integer)
    flag_no_self_delivery = Column( Integer)

class Goods_stat( Base ):
    """ Статусы товара"""
    __tablename__="t_goods_cities"#, metadata,
    city_id=Column( Integer, ForeignKey('t_cities.id'), primary_key=True)
    goods_id=Column( Integer, ForeignKey('t_goods.id'), primary_key=True)
    status=Column( Integer)

class Goods_section( Base ):
    """ Название ВС """
    __tablename__="t_goods_sections"#, metadata,
    guid=Column( Unicode, primary_key=True)
    name=Column( Integer)
                 
class Goods_price( Base ):
    """ Цены товара """
    __tablename__='t_goods_prices'#, metadata,
    price_type_guid=Column( String(), primary_key=True )
    goods_id =Column(Integer, primary_key=True)
    price=Column(Float)
    price_supplier=Column(Float)    

class Goods_block( Base ):
    """ Название инф.блоков"""
    __tablename__='t_goods_block'
    id=Column( Integer, primary_key=True )
    flag_self_delivery=Column( Integer )
    name=Column( Unicode )
    delivery_type=Column( Integer )
    delivery_period=Column( String() )
    flag_permit_delivery = Column( Integer )
    
class Goods_delivery( Base ):
    """ Доставка товаров и цена доставки"""
    __tablename__='t_deliveries'
    goods_id=Column( Integer, ForeignKey('t_goods.id'), primary_key=True )
    city_id=Column( Integer, ForeignKey('t_cities.id') )
    delivery_type=Column( Integer )
    delivery_group=Column( String() )
    highest_price=Column( Integer )

class Shops_block( Base ):
    """Используется только для определения запрещенных инфоблоков"""
    __tablename__='t_shops_block'
    shop_id=Column( Integer, ForeignKey('t_shops.id'), primary_key=True )
    block_id=Column( Integer, primary_key=True )

class Action_goods( Base ):
    """ Содержит список акционных товаров """
    __tablename__='t_action_goods'
    action_id = Column(Integer, ForeignKey('t_actions.id'), primary_key=True )
    set_id = Column(Integer, ForeignKey('t_action_set_price_type.action_set_id'), primary_key=True )
    goods_id = Column(Integer, ForeignKey('t_goods.id'), primary_key=True )

class Actions( Base ):
    """ Список акций """
    __tablename__='t_actions'
    id = Column(Integer, primary_key=True )
    active = Column(Integer)
    action_start = Column(DateTime)
    action_end = Column(DateTime)

class Actions_price( Base ):
    """ Гуид акционной цены """
    __tablename__= 't_action_set_price_type'
    action_set_id = Column( Integer, primary_key=True )
    price_type_guid = Column( String())

class City_price( Base ):
    """ Гуид цен регионов """ 
    __tablename__=  't_city_price_type'
    city_id = Column (Integer, ForeignKey('t_cities.id'), primary_key=True)
    price_type_guid = Column( String())

class Supplier_price( Base ):
    """ Цены поставщика """
    __tablename__='t_goods_prices_supplier'#, metadata,
    price_type_guid=Column( String(), primary_key=True )
    goods_id =Column(Integer, primary_key=True)
    price_supplier=Column(Float)


        
