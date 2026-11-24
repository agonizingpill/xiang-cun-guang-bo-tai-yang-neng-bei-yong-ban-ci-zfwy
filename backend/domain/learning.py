from math import pi,cos,sin
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

def design(hour, clear):
    angle=2*pi*hour/24
    return [sin(angle),cos(angle),sin(2*angle),cos(2*angle),int(clear)]

def calculate(data):
    rows=data['rows']
    train,held=rows[:-6],rows[-6:]
    model=LinearRegression()
    model.fit([design(x['hour'],x['clear']) for x in train],[x['load_wh'] for x in train])
    actual=[x['load_wh'] for x in held]
    predicted=model.predict([design(x['hour'],x['clear']) for x in held])
    target=float(model.predict([design(data['window']['hour'],data['clear'])])[0])
    mae=float(mean_absolute_error(actual,predicted))
    return {'mae':round(mae,3),'plan_wh':round(max(target,0)+mae,3),'held_out':len(held),
           'period':24,'training':len(train)}
