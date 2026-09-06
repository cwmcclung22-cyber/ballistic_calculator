from flask import Flask, request, jsonify
from py_ballisticcalc import *

app = Flask(__name__)

@app.route('/calculate', methods=['POST'])
def calculate_drops():
    # 1. Catch ALL the data dynamically from Supabase
    data = request.json
    
    velocity = float(data.get('velocity'))
    bc = float(data.get('bc'))
    weight = float(data.get('weight'))
    
    # New Dynamic Hardware Variables (with safe fallbacks just in case)
    diameter = float(data.get('diameter', 0.308))
    sight_height = float(data.get('sight_height', 1.5))
    zero_dist = float(data.get('zero', 100.0))
    units = str(data.get('units', 'MOA')).upper()
    
    # Determine angular unit based on the optic
    if units == 'MIL':
        angular_unit = Angular.Mil
    else:
        angular_unit = Angular.MOA
        
    # 2. Build the physics models using the specific rifle's dimensions
    dm = DragModel(bc, TableG1, Weight.Grain(weight), Distance.Inch(diameter))
    ammo = Ammo(dm, mv=Velocity.FPS(velocity))
    weapon = Weapon(sight_height=Distance.Inch(sight_height))
    
    zero_shot = Shot(weapon=weapon, ammo=ammo)
    
    # 3. Create the calculator and set the dynamic zero distance
    calc = Calculator()
    calc.set_weapon_zero(zero_shot, Distance.Yard(zero_dist))
    
    # Fire the simulation
    shot_result = calc.fire(zero_shot, trajectory_range=1000, trajectory_step=Distance.Yard(100))
    
    # 4. Format the drops into the correct unit (MIL or MOA)
    calculated_drops = {}
    for tick in shot_result:
        dist_yards = int(round(tick.distance.get_in(Distance.Yard)))
        if dist_yards % 100 == 0 and dist_yards > 0 and dist_yards <= 1000:
            
            # Extract drop in dynamic angular unit
            drop = abs(tick.drop_adjustment.get_in(angular_unit))
            calculated_drops[f"{dist_yards}yd"] = round(drop, 1)
            
    # 5. Send the math back to Supabase
    return jsonify({"success": True, "drops": calculated_drops})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
