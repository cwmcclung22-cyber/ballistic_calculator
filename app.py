from flask import Flask, request, jsonify
from py_ballisticcalc import *
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/calculate', methods=['POST'])
def calculate_drops():
    try:
        data = request.json
        app.logger.info(f"Received JSON payload: {data}")
        
        # 1. Catch dynamic data with safe fallbacks
        velocity = float(data.get('velocity', 2800))
        bc = float(data.get('bc', 0.450))
        weight = float(data.get('weight', 150))
        diameter = float(data.get('diameter', 0.308))
        sight_height = float(data.get('sight_height', 1.5))
        zero_dist = float(data.get('zero', 100.0))
        units = str(data.get('units', 'MOA')).upper()
        
        # Determine angular output
        if units == 'MIL' or units == 'MRAD':
            angular_unit = Angular.Mil
        else:
            angular_unit = Angular.MOA
            
        app.logger.info(f"Building Physics Models... Vel: {velocity}, Wgt: {weight}, Dia: {diameter}, Zero: {zero_dist}")

        # 2. Build the exact physics models
        dm = DragModel(bc, TableG1, Weight.Grain(weight), Distance.Inch(diameter))
        ammo = Ammo(dm, mv=Velocity.FPS(velocity))
        weapon = Weapon(sight_height=Distance.Inch(sight_height))
        
        # 3. Create the shot and Force a 0.0 degree (level) look angle
        zero_shot = Shot(weapon=weapon, ammo=ammo)
        zero_shot.look_angle = Angular.Degree(0.0) 
        
        # 4. Create calculator and lock zero
        calc = Calculator()
        calc.set_weapon_zero(zero_shot, Distance.Yard(zero_dist))
        
        # 5. Fire simulation to 1000 yards
        shot_result = calc.fire(zero_shot, trajectory_range=1000, trajectory_step=Distance.Yard(100))
        
        calculated_drops = {}
        for tick in shot_result:
            dist_yards = int(round(tick.distance.get_in(Distance.Yard)))
            if dist_yards % 100 == 0 and dist_yards > 0 and dist_yards <= 1000:
                drop = abs(tick.drop_adjustment.get_in(angular_unit))
                calculated_drops[f"{dist_yards}yd"] = round(drop, 1)
                
        app.logger.info(f"Math Successful! Output: {calculated_drops}")
        return jsonify({"success": True, "drops": calculated_drops})

    except Exception as e:
        app.logger.error(f"Engine Crash: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
