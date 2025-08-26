BUILDING = '/building'
FLOOR = '/floor'
ROUTE = '/route'
SCAN = '/scan'
PREDICT = '/predict'


ADD_BUILDING= f'{BUILDING}/add'
BUILDING_UPDATE_DOORS_NAME = f'{BUILDING}/updateDoorsName'
BUILDING_GET_PATH = f'{BUILDING}/getPath'
BUILDING_GET_SVG_DIRECT = f'{BUILDING}/getSvgDirect'
BUILDING_GET_BUILDINGS = f'{BUILDING}/getBuildings'
ADD_FLOOR = f'{FLOOR}/add'
CALIBRATE_FLOOR = f'{FLOOR}/calibrate'
GET_SVG_DIRECT = f'{FLOOR}/getSvgDirect'
GET_FLOOR_DATA = f'{FLOOR}/getData'
UPDATE_DOORS_NAMES = f'{FLOOR}/updateDoorsNames'
FLOOR_GET_ROUTE = f'{FLOOR}{ROUTE}/get'
GET_ALL_BUILDINGS = f'{BUILDING}/get'
GET_ALL_DOORS = f'{FLOOR}/getDoors'
GET_GRID_SVG = f'{FLOOR}/getGridSvg'
ADD_BUILDING = f'{BUILDING}/add'
GET_FLOORS = f'{BUILDING}/getFloors'
ADD_SCAN = f'{FLOOR}/{SCAN}'
UPLOAD_SCAN = f'{FLOOR}/{SCAN}/upload'
CONCAT_SCAN = f'{FLOOR}/{SCAN}/concat'
GET_ONE_CM_SVG = f'{FLOOR}/getOneCmSvg'

START_PREDICT = f'{PREDICT}/start'
GET_PREDICT = f'{PREDICT}/get'
PREDICT_TOP1 = f'{PREDICT}/top1'
PREDICT_TOP5 = f'{PREDICT}/top5'



#parameters
BUILDING_ID = 'buildingId'
DOOR_ID = 'doorId'
FLOOR_ID = 'floorId'
SIZE = 800

