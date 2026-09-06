from flask import Flask, request, jsonify
from py_ballisticcalc import *

app = Flask(__name__)

@app.route('/calculate', methods=['POST'])
def calculate_drops():
    # 1. Catch the data from your Supabase Edge Function
    data = request.json
    velocity = float(data.get('velocity'))
    bc = float(data.get('bc'))
    
    # 2. Build the new physics models
    # Set the G1 profile and assign the Muzzle Velocity (mv)
    dm = DragModel(bc, TableG1)
    ammo = Ammo(dm, mv=Velocity.FPS(velocity))
    
    # Set 1.5-inch scope height 
    weapon = Weapon(sight_height=Distance.Inch(1.5))
    
    # Combine them into a Shot profile
    zero_shot = Shot(weapon=weapon, ammo=ammo)
    
    # 3. Create the calculator and zero the rifle at 100 yards
    calc = Calculator()
    calc.set_weapon_zero(zero_shot, Distance.Yard(100))
    
    # Fire the mathematical simulation out to 1000 yards
    shot_result = calc.fire(zero_shot, trajectory_range=1000, trajectory_step=Distance.Yard(100))
    
    # 4. Format the drops into a clean JSON dictionary
    calculated_drops = {}
    
    for tick in shot_result:
        # Extract the distance and the drop in MOA
        dist_yards = int(round(tick.distance.get_in(Distance.Yard)))
        
        # Save drops at 100-yard increments
        if dist_yards % 100 == 0 and dist_yards > 0 and dist_yards <= 1000:
            moa_drop = abs(tick.drop_adjustment.get_in(Angular.MOA))
            calculated_drops[f"{dist_yards}yd"] = round(moa_drop, 1)
            
    # 5. Send the math back to Supabase
    return jsonify({"success": True, "drops": calculated_drops})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
