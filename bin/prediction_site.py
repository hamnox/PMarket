import web
import prediction_runner as pRun

urls = (
  '/', 'index'
) #list of urls and what classes they match. when http tries (it will try these first), lpthw.web will load that class to handle the request.

app = web.application(urls, globals()) #deleted this but it didn't do anthing WHAT O_O

render = web.template.render('templates/') #Get a template, slob

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
                return "yay!"
            except KeyError:
                pRun.add_prediction("predictions.json",form.predictionid,form.statement,50)
                pRun.add_bet("predictions.json",form.username,form.predictionid,float(form.credence))
                return "Sorry"

if __name__ == "__main__":
    app.run()