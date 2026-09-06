from flask import Flask, request, jsonify
from py_ballisticcalc import *

app = Flask(__name__)

@app.route('/calculate', methods=['POST'])
def calculate_drops():
    # 1. Catch the data from your Supabase Edge Function
    data = request.json
    velocity = float(data.get('velocity'))
    bc = float(data.get('bc'))
    weight = float(data.get('weight'))
    
    # 2. Run the Gehtsoft Ballistics Math
    calc = Calculator()
    
    # Set the bullet data dynamically from your database
    ammo = Ammo(
        weight=Weight.Grain(weight),
        velocity=Velocity.FPS(velocity)
    )
    ammo.set_g1(bc) # Set the specific drag profile
    
    # Set a standard 100-yard zero and 1.5-inch scope height
    weapon = Weapon(
        zero_distance=Distance.Yard(100),
        sight_height=Distance.Inch(1.5)
    )
    
    # Calculate the trajectory out to 1000 yards
    trajectory = calc.fire(ammo, weapon, Atmo())
    
    # 3. Format the drops into a clean list for the DOPE card
    calculated_drops = {}
    
    # Loop through the flight path and grab the MOA drop for our 100-yard increments
    for tick in trajectory:
        dist_yards = int(tick.distance(Distance.Yard).value)
        
        # If the distance is exactly 100, 200, 300... up to 1000
        if dist_yards % 100 == 0 and dist_yards <= 1000:
            # Save the drop in MOA (rounded to 1 decimal place)
            moa_adjustment = abs(tick.drop_adjustment(Angular.MOA).value)
            calculated_drops[f"{dist_yards}yd"] = round(moa_adjustment, 1)
            
    # 4. Send the real math back to Supabase
    return jsonify({"success": True, "drops": calculated_drops})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
