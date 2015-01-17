import web
import time
import __builtin__
import prediction_runner as pRun

urls = (
  '/', 'index', '/scores', "scores", '/lookup', 'lookup', "/settle", "settle"
) #list of urls and what classes they match. when http tries (it will try these first), lpthw.web will load that class to handle the request.

app = web.application(urls, globals()) #deleted this but it didn't do anthing WHAT O_O
render = web.template.render('templates/',base="layout", globals={'time':time, 'str':__builtin__.str}) #Get a template, slob

class index:
    def GET(self):
        form = web.input(username="tester")
        return render.index(username = form.username) #notice how we specifically picked INDEX as the html template.

    def POST(self):
        form = web.input(username=None,statement=None,credence=None,predictionid=None,housebet=50,tags="") # look up how to add tags later
        if None in form:
            raise ValueError
        else:
            pRun.add_prediction("predictions.json",form.predictionid,form.statement,50,form.tags)
            pRun.add_bet("predictions.json",form.username,form.predictionid,float(form.credence))
            pRun.score("predictions.json", "testusers.json")
            info = pRun.get_prediction_info("predictions.json", form.predictionid)
            return render.display_table(json=info,predictionid=form.predictionid)

class scores:
    def GET(self):
        userreturn = pRun.score("predictions.json", "testusers.json")
        return render.display_table(json=userreturn,predictionid=False) #woops predictionid is invalid here.

class lookup:
    def GET(self):
        return render.retrieve(defaultid="test")

    def POST(self):
        form = web.input(predictionid="")
        info = pRun.get_prediction_info("predictions.json", form.predictionid)
        return render.display_table(json=info,predictionid=str(form.predictionid))
    
class settle:
    def POST(self):
        form = web.input(predictionid="", truthvalue=None)
        info = pRun.settle_bet("predictions.json",form.predictionid, form.truthvalue)
        return render.display_table(json=info,predictionid=form.predictionid)
    
if __name__ == "__main__":
    app.run()

