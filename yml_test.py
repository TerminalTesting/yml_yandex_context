#! /usr/bin/python
# -*- coding: utf8 -*-
     
#import pytest
import unittest
import sys
from lxml import etree
import codecs 
import urllib2
import os
from yml_models import *
from string import split
from urlparse import urlparse

def get_domain(url):
    """  найти домен региона """
    url_tuple=urlparse(url)
    netloc=split( url_tuple[1], '.')
    return unicode(netloc[0])

XSD_LIST={
          'YML Yandex TYPICAL':'shops.xsd',
          'YML Yandex CONTEXT':'shops-context.xsd',
          'YML Yandex CPA':'shops-cpa.xsd',
          'SERIES & BRANDS':'series-brands.xsd'         
          }

DTD_LIST={
          'YML Yandex TYPICAL':'shops.dtd',
          'YML Yandex CONTEXT':'shops-context.dtd',
          'YML Yandex CPA':'shops-cpa.dtd',
          'SERIES & BRANDS':'series-brands.dtd'         
          }


class YMLTest(unittest.TestCase):
    """Тесты ядекс выгрузки"""
    WAIT_TIME = 60
    SLEEP_TIME=1
    XSD_DTD_CATALOG='./xsd_dtd/'
    DTD_FILE_NAME=XSD_DTD_CATALOG+DTD_LIST[ os.getenv('TYPE')]
    XSD_FILE_NAME=XSD_DTD_CATALOG+XSD_LIST[ os.getenv('TYPE')]
    YML_FILE_NAME='XML_FILE_NAME'

    # домен региона для которого проверяется выгрузка
    CITY_DOMAIN='nsk'
    
    #соединение с БД
    HOST = os.getenv('HOST')
    PORT = os.getenv('PORT')
    SCHEMA = os.getenv('SCHEMA')
    USER = os.getenv('USER')
    PSWD = os.getenv('PSWD')

    # максимальное кол-во предложений для проверки
    MAX_OFFERS = 1000
        
    def setUp(self):
        """ инициализация переменных для всех тестов"""
        pass
        self.parser = etree.XMLParser(huge_tree=True)
        print os.getenv('TYPE')
        print self.DTD_FILE_NAME
        print self.XSD_FILE_NAME
        self.CONNECT_STRING=('mysql://%s:%s@%s:%s/%s?charset=utf8')%(self.USER, self.PSWD, self.HOST, self.PORT, self.SCHEMA     )
    
    def tearDown(self):
        """Удаление переменных для всех тестов. Остановка приложения"""
        if sys.exc_info()[0]:   
            print sys.exc_info()[0]

    def test_yml_0(self):
        """ верификация по dtd описанию shops.dtd """
        xml=etree.parse(self.YML_FILE_NAME, parser=self.parser )
        dtd=etree.DTD(codecs.open(self.DTD_FILE_NAME))
        result= dtd.validate(xml)
        error_msg=dtd.error_log.filter_from_errors()
        try:
            dtd.assertValid(xml)
        except:
            print '\nОШИБКА ВАЛИДАЦИИ XML ФАЙЛА ПО DTD ОПИСАНИЮ'
            print '-'*80
            msg = error_msg.last_error.message.replace('Element offer content does not follow the DTD, expecting',
                                                       'Контент элемента <offer> не соответствует DTD. Ожидалось:\n'.decode('utf-8')).replace(', got', '\n\nПолучено:\n'.decode('utf-8'))
            print 'Сообщение об ошибке:\n'
            print msg
            raise AssertionError
        print ('YML:%s\nDTD:%s\n\nDTD Validation successful.')%(self.YML_FILE_NAME, self.DTD_FILE_NAME )

    def test_yml_1(self):
        """ верификация по xsd описанию shops.xsd """
        xml=etree.parse(self.YML_FILE_NAME, parser=self.parser, base_url=None)
        xsd=etree.XMLSchema(file=self.XSD_FILE_NAME)
        stat=xsd.validate(xml)
        error_msg=xsd.error_log.filter_from_errors()
        try:
            xsd.assertValid(xml)
        except:
            print '\nОШИБКА ВАЛИДАЦИИ XML ФАЙЛА ПО XSD ОПИСАНИЮ'
            print '-'*80
            print ('File:%s\nLine:%s\n\nError message:\n%s')%(self.YML_FILE_NAME, error_msg.last_error.line, error_msg.last_error.message   )
            raise AssertionError
        print ('YML:%s\nXSD:%s\n\nXSD Validation successful.')%(self.YML_FILE_NAME, self.XSD_FILE_NAME )

     
    def test_yml_2(self):
        """ проверка тегов на соответствие с базой """
        db = create_engine(self.CONNECT_STRING) #, convert_unicode=False
        db.echo = False  # Try changing this to True and see what happens
        metadata = MetaData(db)
        session=create_session(bind=db)
        xml=etree.parse(self.YML_FILE_NAME, parser=self.parser )
        xml_tree=xml.getiterator('offer')
        shop_url_element=xml.find('shop').find('url')
        
        DOMAIN = get_domain(shop_url_element.text) 
        cnt=1
        stat=0
        
        # возможность доставки для региона
        delivery=session.query( Region, Goods_delivery, Goods_price).\
                        join(Goods_delivery, (Region.id==Goods_delivery.city_id) ).\
                        join(Goods_price, (Goods_delivery.goods_id==Goods_price.goods_id)  ).\
                        filter(Region.domain==DOMAIN).\
                        filter( (Region.id==Goods_stat.city_id ) & (Goods_price.price_type_guid==Region.price_type_guid) ).\
                        all()

        #если возможности доставки нет то тег delivery=False
        delivery_flag=len(delivery)>0
        # список цен на доставку в зависимости от габаритности товара
        if delivery_flag==True:
            delivery_price_1=[ float(element[2].price) for element in delivery if element[1].delivery_type==1 ]
            delivery_price_2=[ float(element[2].price) for element in delivery if element[1].delivery_type==2 ]
            delivery_price={1:delivery_price_1, 2:delivery_price_2}
#             highest_price=[ float(element[1].highest_price) if element[1].highest_price!=None else 0.00 for element in delivery  ]
            highest_price=[ float(element[1].highest_price) if element[1].highest_price!=None else None for element in delivery if element[1].delivery_group=='city'  ]
#             pass
#         else:
#             delivery_price={1:0.00, 2:0.00}
        
        print ('YML:%s\nDomain:%s\nDeliveries flag:%s')%(self.YML_FILE_NAME, DOMAIN, delivery_flag )
        for element in xml_tree:
            # получаем теги из выгрузки
            price_tag=element.find('price')
            store_tag=element.find('store')
            pickup_tag=element.find('pickup')
            #rконтекстная выгрузка
            try:
                vendor_tag=unicode( element.find('vendor').text ) if element.find('vendor').text !=None else ''
            except AttributeError:
                vendor_tag=''
            try:
                type_prefix_tag=element.find('typePrefix')
            except AttributeError:
                type_prefix_tag=''
            try:    
                model_tag=unicode( element.find('model').text ) if element.find('model').text !=None else ''
            except AttributeError:
                model_tag=''
            
            description_tag=element.find('description')
            delivery_price_tag=element.find('local_delivery_cost') if element.find('local_delivery_cost')!=None else xml.find('shop').find('local_delivery_cost')
            
            delivery_tag=element.find('delivery')

            cnt+=1
            # получаем параметры товара из БД
            item=session.query( Goods, Goods_stat, Region, Goods_price, Goods_section,
                                Goods_block.name, Goods_block.delivery_type, Goods_block.flag_self_delivery,
                                Goods.overall_type, Goods_block.flag_permit_delivery, Goods_block.id ).\
                                join(Goods_stat, Goods.id==Goods_stat.goods_id).\
                                join(Goods_price, (Goods.id==Goods_price.goods_id)  ).\
                                join(Goods_section, (Goods_section.guid==Goods.section_guid)  ).\
                                join(Goods_block, (Goods_block.id==Goods.block_id) ).\
                                filter(Goods.id==element.attrib['id']).\
                                filter(Region.domain==DOMAIN).\
                                filter( (Goods_stat.city_id== Region.id) & (Goods_price.price_type_guid==Region.price_type_guid) ).\
                                first()
            
            no_self_delivery = []
            no_self_delivery.append( session.query(Shops.flag_no_self_delivery ).\
                                     join( Region, Shops.city_id==Region.id ).\
                                     filter( Region.domain==DOMAIN ).\
                                     all())
                
            no_self_delivery.append( session.query( Shops.flag_no_self_delivery_kbt ).\
                                     join( Region, Shops.city_id==Region.id ).\
                                     filter( Region.domain==DOMAIN ).\
                                     all())
              

            # в выгрузке есть а в БД нет ид товара
            if item==None:
                print 'Ошибка в теге <OFFER>:'
                print 'ID товара: ', element.attrib['id'] ,' значение в файле:',description_tag.text, ' значение в базе данных не найдено'
                print '-'*80
                continue

            item_vendor=unicode( item[0].brand ) if item[0].brand !=None else ''
            item_model= (' ' + item[0].model_name) if item[0].model_name !=None else ' '

            #тег название товара <description>
#             if description_tag.text!=item[0].name:
#                 print 'Error:NAME:', element.attrib['id'] ,' XML:',description_tag.text, ' DB:', item[0].name

            #тег цена <price>
            if int(float(price_tag.text)) == 0:
                stat+=1
                print 'Ошибка в теге <PRICE>:'
                print 'ID товара: ', element.attrib['id'] ,' Цена у данного товара равна нулю. '
                print '-'*80

            else:
                actions_goods = session.query(Action_goods).group_by(Action_goods.action_id).\
                                                            filter(Action_goods.goods_id == item[0].id).\
                                                            filter(Action_goods.action_id != 63 ).all() #63 - акция лояльности, не должно попадать в выгрузку.
                if actions_goods: 
                    if len(actions_goods)>1:
                        stat+=1
                        print 'ID товара: ', element.attrib['id'] ,' Данный товар участвует одновременно в 2 активных акциях, необходима ручная проверка наименования'
                        print '-'*80

                    action_price_guid = session.query(Actions_price.price_type_guid).filter(Actions_price.action_set_id == actions_goods[0].set_id).all()
                    if action_price_guid:
                        action_price_guid = (x[0] for x in set(action_price_guid))#guid акционной цены товара во всех регионах
                        good_price = session.query(City_price.price_type_guid).filter(City_price.city_id == item[2].id).filter(City_price.price_type_guid.in_(action_price_guid)).all()[0][0] #guid акционной цены товара в нужном регионе
                        action_price = session.query(Goods_price.price).filter(Goods_price.price_type_guid == good_price).filter(Goods_price.goods_id == item[0].id).all()
                        if action_price:
                            
                            action_price = action_price[0][0]
                            main_price = item[3].price if item[1].status != 5 else item[3].price_supplier

                            if int(action_price) > int(main_price) and actions_goods[0].action_id not in (13,):
                                item_price = main_price
                            elif int(action_price) < int(main_price) and actions_goods[0].action_id in (13,):
                                item_price = main_price
                            else:
                                item_price = action_price


                            if int(float(price_tag.text)) != int(item_price):
                                stat+=1
                                print 'Ошибка в теге <PRICE>: ЦЕНА АКЦИОННАЯ'
                                print 'ID товара: ', element.attrib['id'] ,' значение в файле:', int(float(price_tag.text)), ' значение в базе данных:', int(item_price)
                                print '-'*80

                        else:
                            item_price = item[3].price if item[1].status != 5 else item[3].price_supplier            
                            if int(float(price_tag.text))!= int(item_price):
                                stat+=1
                                print 'Ошибка в теге <PRICE>:'
                                print 'ID товара: ', element.attrib['id'] ,' значение в файле:',int(float(price_tag.text)), ' значение в базе данных:', int(item_price)
                                print '-'*80

                       
                    else:
                        item_price = item[3].price if item[1].status != 5 else item[3].price_supplier            
                        if int(float(price_tag.text))!= int(item_price):
                    
                            stat+=1
                            print 'Ошибка в теге <PRICE>:'
                            print 'ID товара: ', element.attrib['id'] ,' значение в файле:',int(float(price_tag.text)), ' значение в базе данных:', int(item_price)
                            print '-'*80


                else:
                    item_price = item[3].price if item[1].status != 5 else item[3].price_supplier            
                    if int(float(price_tag.text))!= int(item_price):
                    
                        stat+=1
                        print 'Ошибка в теге <PRICE>:'
                        print 'ID товара: ', element.attrib['id'] ,' значение в файле:',int(float(price_tag.text)), ' значение в базе данных:', int(item_price)
                        print '-'*80




            #тег статуса <available>
            if (element.attrib['available'] in ('true', 'True') ) != ( item[1].status==1 ):
                stat+=1
                print 'Ошибка в теге <AVAILABLE>:'
                print 'ID товара: ', element.attrib['id'] ,' значение в файле:',element.attrib['available'], ' значение в базе данных:',item[1].status==1, item[1].status
                print '-'*80
                
            #тег самовывоза <pickup>, может быть разным при разной габаритности и насткойках инфоблоков
            #не учтены маловероятные варианты, например, если в регионе 2 магазина и в настройках их обоих запрещен вывод МГТ и т.д. В настоящий момент на сайте нигде это не используется
            pickup=True

            if int( item[8] ) > 0:#если габаритность переопределена в карточке товара, 1 - обычная, 2 - крупногабаритный
                if int( item[8] )==1 and ((0,) not in no_self_delivery[0]):
                    pickup=False
                if int( item[8] )==2 and ((0,) not in no_self_delivery[1]):
                    pickup=False
                if int( item[8] )==2 and item[9] == 1:
                    pickup=False
                if len(no_self_delivery[0])==1 and int( item[8] )==1:
                    nomgt = session.query(Shops_block.block_id).\
                                          join(Shops, Shops_block.shop_id==Shops.id).\
                                          join(Region, Shops.city_id==Region.id).\
                                          filter(Region.domain==DOMAIN).\
                                          all()
                    if nomgt == True and int(item[10]) in nomgt:
                        pickup=False
                    
            else:
                if int( item[6] )==1 and ((0,) not in no_self_delivery[0]):
                    pickup=False
                if int( item[6] )==2 and ((0,) not in no_self_delivery[1]):
                    pickup=False
                if int( item[6] )==2 and item[9] == 1:
                    pickup=False
                if len(no_self_delivery[0])==1 and int( item[6] )==1:
                    nomgt = session.query(Shops_block.block_id).\
                                          join(Shops, Shops_block.shop_id==Shops.id).\
                                          join(Region, Shops.city_id==Region.id).\
                                          filter(Region.domain==DOMAIN).\
                                          all()
                    if nomgt == True and int(item[10]) in nomgt:
                        pickup=False
                    
            if (pickup_tag.text in ('true', 'True') ) != pickup:
                   
                stat+=1
                print 'Ошибка в теге <PICKUP>:'
                print 'ID товара: ', element.attrib['id'] ,' значение в файле:',pickup_tag.text, ' необходимое значение:', pickup
                print '-'*80
              
                
            #тег склад <store>
            if (store_tag.text in ('true', 'True') ) != ( item[1].status==1 ):
                stat+=1
                print 'Ошибка в теге <STORE>:'
                print 'ID товара: ', element.attrib['id'] ,' значение в файле:', store_tag.text, ' значение в базе данных:', item[1].status==1, item[1].status
                print '-'*80

            #тег доставка <delivery>
            if (delivery_tag.text.strip() in ('true', 'True') )!=(delivery_flag):
                stat+=1
                print 'Ошибка в теге <DELIVERY>:'
                print 'ID товара: ', element.attrib['id'] ,' значение в файле:', delivery_tag.text, ' значение в базе данных:', delivery_flag
                print '-'*80
            #тег производитель <vendor>
#             if vendor_tag.text==None:
#                 print 'Error: tag <VENDOR>:', element.attrib['id'] ,' XML:', vendor_tag.text, ' DB:', item[0].brand
            if (vendor_tag )!=(item_vendor):
                stat+=1
                print 'Ошибка в теге <VENDOR>:'
                print 'ID товара: ', element.attrib['id'] ,' значение в файле:', vendor_tag.text, ' значение в базе данных:', item[0].brand
                print '-'*80

            #для контекстной выгрузки
            if (model_tag )!=(item_model):
                stat+=1
                print 'Ошибка в теге <MODEL_NAME>:'
                print 'ID товара: ', element.attrib['id'] ,' значение в файле:', model_tag, len(model_tag), 'симв.', ' значение в базе данных:', item_model, len(item_model), 'симв.'
                print '-'*80

            #если цены доставки определены, а тега local_delivery_cost нет             
            if (delivery_flag==True) and (delivery_price_tag==None):
                stat+=1
                print 'Ошибка в теге <LOCAL_DELIVERY_COST>:'
                print 'Цена доставки определена, а тега <LOCAL_DELIVERY_COST> нет'
                print 'ID товара: ', element.attrib['id'] ,' значение в файле:', delivery_price_tag, ' значение в базе данных:', delivery_flag
                print '-'*80

            #цена доставки товара в списке цен доставок по региону и по габаритности .delivery_type
            if (delivery_flag==True):
                # цена доставки нулевая, то проверяем ценовой предел 
                if float(delivery_price_tag.text)==0.00:
                    # при бесплатной доставке цена товара д.б больше чем предел
                    if float(price_tag.text)<max(highest_price) or highest_price[int( item[6] )-1 ]==None:               
                        stat+=1
                        print 'Ошибка в теге <LOCAL_DELIVERY_COST>:'
                        print 'Бесплатная доставка при цене меньше требуемой'
                        print 'ID товара: ', element.attrib['id'] ,' значение в файле:', delivery_price_tag.text, ' значение в базе данных:', price_tag.text
                        print '-'*80

                #цена доставки определена в товаре или для магазина
                else:
                    if int( item[8] ) > 0:
                        if  ( float(delivery_price_tag.text) not in delivery_price[ int( item[8] ) ] ): 
                            stat+=1
                            print 'Ошибка в теге <LOCAL_DELIVERY_COST>:'
                            print 'Цена доставки определена в товаре или для магазина'
                            print 'ID товара: ', element.attrib['id'] ,' значение в базе данных:', delivery_price_tag.text, ' тип доставки(1-МГТ, 2-КГТ):', int( item[8] )
                            print '-'*80
                            
                    else:
                        if  ( float(delivery_price_tag.text) not in delivery_price[ int( item[6] ) ] ): 
                            stat+=1
                            print 'Ошибка в теге <LOCAL_DELIVERY_COST>:'
                            print 'Цена доставки определена в товаре или для магазина'
                            print 'ID товара: ', element.attrib['id'] ,' значение в базе данных:', delivery_price_tag.text, ' тип доставки(1-МГТ, 2-КГТ):', int( item[6] )
                            print '-'*80
 
          
        # конец теста
        assert stat==0, (u'Errors:%d')%(stat)
    
    def test_yml_3(self):
        """  проверка корректности ( доступности ) ссылки на товар (полный перебор тест длится около 4 часов)"""
        xml=etree.parse(self.YML_FILE_NAME, parser=None )
        xml_tree=etree.iterwalk(xml, events=("start", "end"), tag="url" )
        cnt=1
        stat=0
        for element in xml_tree:
    	    try:
                link=urllib2.urlopen(element[1].text, None, self.WAIT_TIME)
    	    except:
                print ('%d.Stat:%d Link:%s')%(cnt, link.code, element[1].text )
                stat +=1
            cnt+=1
            if cnt>=self.MAX_OFFERS: 
                break
        assert stat==0, (u'Bad links find:%d')%(stat)


