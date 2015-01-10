import web
import time
import __builtin__
import prediction_runner as pRun

urls = (
  '/', 'index', "/scores", "scores"
) #list of urls and what classes they match. when http tries (it will try these first), lpthw.web will load that class to handle the request.

app = web.application(urls, globals()) #deleted this but it didn't do anthing WHAT O_O
render = web.template.render('templates/',base="layout", globals={'time':time, 'str':__builtin__.str}) #Get a template, slob

class index:
    def GET(self):
        form = web.input(username="NoBody")
        # greeting = "Hello, %s" % form.name # this is how you use the ?x=y values
        # return greeting # this would just return the text.

        return render.index(username = form.username) #notice how we specifically picked INDEX as the html template.

    def POST(self):
        form = web.input(username=None,statement=None,credence=None,predictionid=None,housebet=50) # look up how to add tags later
        if None in form:
            raise ValueError
        else:
            try:
                jsonreturn = pRun.add_bet("predictions.json",form.username,form.predictionid,float(form.credence))
                return render.display_table(json=jsonreturn)
            except KeyError:
                #if only I knew a way to make it put a javascript box up here
                pRun.add_prediction("predictions.json",form.predictionid,form.statement,50)
                jsonreturn = pRun.add_bet("predictions.json",form.username,form.predictionid,float(form.credence))
                return render.display_table(json=jsonreturn)

class scores:
    def GET(self):
        userreturn = pRun.score("predictions.json", "testusers.json")
        return render.display_table(json=userreturn)
if __name__ == "__main__":
    app.run()