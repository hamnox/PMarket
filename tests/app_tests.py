from nose.tools import *
from bin.prediction_site import app
from tests.tools import assert_response

def test_index():
    #check that we get a 404 on the / URL
    resp = app.request("/")
    assert_response(resp,status="200")
    
    #test GET request
    resp = app.request("/")
    assert_response(resp,contains="user")
    
    #make sure default values work for the form, except we don't want that
    #resp = app.request("/",method="POST")
    #assert_response(resp)
    
    #test that we get expected values
    #data = {'name':'Zed','greet':'Hola'} # not our page's problem
    #resp = app.request("/hello",method="POST",data=data)
    #assert_response(resp,contains="Zed")