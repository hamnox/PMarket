import web
import prediction_runner as pRun

urls = (
  '/', 'index'
) #list of urls and what classes they match. when http tries (it will try these first), lpthw.web will load that class to handle the request.

app = web.application(urls, globals()) #deleted this but it didn't do anthing WHAT O_O

render = web.template.render('templates/',base="layout") #Get a template, slob

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
                pRun.add_bet("predictions.json",form.username,form.predictionid,float(form.credence))
                return "It went through just fine dearie"
            except KeyError:
                #if only I knew a way to make it put a javascript box up here
                pRun.add_prediction("predictions.json",form.predictionid,form.statement,50)
                pRun.add_bet("predictions.json",form.username,form.predictionid,float(form.credence))
                return render.message(msg="Couldn't find that ID, had to make a new prediction")
         #   import json
          #  jsonfile = open("predictions.json",'r')
           # return render.display_table(json.loads(jsonfile.read()))
if __name__ == "__main__":
    app.run()