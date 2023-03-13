import cognit
 
requirements = { } 
 
def inference(smart_meter_data, weather_data, model_file):
      model.loadl(model_file)
      model.evaluate()
      return model.inference(weather_data, ….)
 
ctx = cognit.new(requirements) 
 
ctx.copy('http://path/to/bucket/weather_prediction.csv', faas:'/data/weather_prediction.csv') 
 
ctx.copy('http://path/to/bucket/model.torch', faas:'/data/model.torch')
 
charge_complete = False
while not charge_complete:
	smart_meter_data = smartmeter.get_data() 
    prediction = ctx.FunctionEvaluate(inference, smart_meter_data, '/data/weather.csv', '/data/model.torch')
	charge_complete = smartmeter.check_charge()
