import csv
from itertools import product


# INDIVIDUAL GEAR RESTRICTIONS
min_bore = 18 # minimum bore diameter (mm)
max_teeth = 70 # max number of teeth on any gear
max_gear_length = 5 * 25.4 # max length of any one gear (mm)
min_thickness = 2 # minimum gear thickness (in)

min_fos = 1.3 # minimum factor of safety (per gear)
max_fos = 2.25 # maximum factor of safety (per gear)

# COMBINATION RESTRICTIONS
min_ratio = 3.4 # minimum viable gear ratio
max_ratio = 3.6 # maximum viable gear ratio
max_mass = 4 # maximum mass of all gears (kg)
min_length = 7 * 25.4 # minimum center to center length (mm)

# TORQUE!
max_CVT = 3.9 # max CVT reduction - used to determine torque on gears
engine = 25 # max engine torque (Nm) - used to determine torque on gears


class Gear: 
    def __init__(self, a , b, c, d, e, f, g, h, i, j):
        self.num_teeth, self.thickness, self.name, self.torque, self.bore1, \
            self.bore2, self.weight1, self.weight2, self.pitchd, self.formfactor \
            = int(a), float(b), c, float(d), int(e), int(f), float(g), \
            float(h), float(i), j

    def __str__(self):
        # return gear name: nteeth_thickness
        return self.name
    
    # when used as a number, represented by the number of teeth
    def int(self):
        return self.num_teeth

class gear_combination: 
    """A gear_combination stores data about the four gears, including the total mass, total reduction, and factors of safety"""
    def __init__(self, gears, gear2bore, gear3bore, mass2, mass3):
        gear1 = gears[0]
        gear2 = gears[1]
        gear3 = gears[2]
        gear4 = gears[3]
        
        self.gears = [gear1, gear2, gear3, gear4]
        self.bores = [gear1.bore2, gear2bore, gear3bore, gear4.bore1]

        # center-to-center length from first to last gear
        self.length = (gear1.pitchd + gear2.pitchd + \
            gear3.pitchd + gear4.pitchd) / 2

        # two-stage reduction
        self.reduction1 = gear2.num_teeth / gear1.num_teeth
        self.reduction2 = gear4.num_teeth / gear3.num_teeth
        self.totalreduction = round((self.reduction1 * self.reduction2), 3)

        # first gear uses second weight because we use the larger bore
        # second gear uses the first weight because we use the smaller bore
        self.initalmass = round((float(mass2) + float(mass3) + gear1.weight2 + gear4.weight1), 3)

        # FOS = allowable torque / applied torque
        # applied torque changes based on reduction
        fos1 = round((gear1.torque / (engine * max_CVT)), 3)
        fos2 = round((gear2.torque / (engine * max_CVT * self.reduction1)), 3)
        fos3 = round((gear3.torque / (engine * max_CVT * self.reduction1)), 3)
        fos4 = round((gear4.torque / (engine * max_CVT * self.totalreduction)), 3)
        self.fos = [fos1, fos2, fos3, fos4]

        
        # reduce width to minimize mass -> decrease to min FOS
        # each pair of gears (1&2 and 3&4) will have matching widths
        # assume gears 1&3 always have a lower FOS than 2&4 respectively
        self.width1 = round(float(min_fos / fos1) * float(gear1.thickness), 3)
        self.width2 = round(float(min_fos / fos3) * float(gear3.thickness), 3)

        # update FOS values, 1&3 are decreased to minimum
        self.newfos2 = round(fos2 * self.width1 / gear2.thickness, 3)
        self.newfos4 = round(fos4 * self.width2 / gear4.thickness, 3)
        self.newfos = [min_fos, self.newfos2, min_fos, self.newfos4]

        # calculate new mass after reducing thickness
        self.newmass = round((self.width1 / gear1.thickness) * (gear1.weight2 + mass2) \
            + (self.width2 / gear3.thickness) * (gear4.weight1 + mass3), 3)

        # store gear info in list for easy printing to CSV later
        self.info = [gear1, gear1.weight2, gear1.pitchd, min_fos, self.width1,
            gear2, mass2, gear2.pitchd, self.newfos2, self.width1,
            gear3, mass3, gear3.pitchd, min_fos, self.width2,
            gear4, gear4.weight1, gear4.pitchd, self.newfos4, self.width2,
            self.totalreduction, self.reduction1, self.reduction2,
            self.newmass, self.length
        ]

        # convert all values in info to strings
        for i in range(len(self.info)):
            if not isinstance(self.info[i], str):
                self.info[i] = str(self.info[i])

# READ SHEET OF GEARS
def read_gear_sheet():
    # gear data stored in CSV
    with open("KHK MSGA1 Gears.csv") as f:
        r = csv.reader(f)
        all_gears = [row for row in r]
        all_gears.pop(0) # remove header row
    
    if len(all_gears) == 0:
        print("No gear data found.")
        return

    # return only "good gears" - fit restrictions
    return [Gear(*gear[0:10]) for gear in all_gears if good_gear(gear)]   

# CHECK INDIVIDUAL GEAR FITS RESTRICTIONS
def good_gear(gear_info):
    return int(gear_info[0]) <= max_teeth and \
        float(gear_info[8]) <= max_gear_length and \
        (float(gear_info[4]) >= min_bore or float(gear_info[5]) >= min_bore) and \
        float(gear_info[1]) >= min_thickness

# FIND POSSIBLE GEAR COMBINATIONS
def possible_gear_combos(all_gears):
    viable_combos = []

    for gears in product(all_gears, repeat = 4):
        # gear ratio is the product of the two reductions
        gear_ratio = (gears[1].num_teeth / gears[0].num_teeth) * \
            (gears[3].num_teeth / gears[2].num_teeth)
        
        if min_ratio < gear_ratio < max_ratio and \
            gears[0].thickness == gears[1].thickness and \
            gears[2].thickness == gears[3].thickness and \
            all(gears[i].pitchd <= max_gear_length for i in range(0, 4)):


            # check that gears 2 and 3 match in bore diameter
            if gears[1].bore1 >= min_bore:
                if gears[1].bore1 == gears[2].bore1:
                    viable_combos.append(gear_combination(gears, \
                        gears[1].bore1, gears[2].bore1, \
                        gears[1].weight1, gears[2].weight1))
                elif gears[1].bore1 == gears[2].bore2:
                    viable_combos.append(gear_combination(gears, \
                        gears[1].bore1, gears[2].bore2, \
                        gears[1].weight1, gears[2].weight2))
            if gears[1].bore2 >= min_bore:
                if gears[1].bore2 == gears[2].bore1:
                    viable_combos.append(gear_combination(gears, \
                        gears[1].bore2, gears[2].bore1, \
                        gears[1].weight2, gears[2].weight1))
                elif gears[1].bore2 == gears[2].bore2:
                    viable_combos.append(gear_combination(gears, \
                        gears[1].bore2, gears[2].bore2, \
                        gears[1].weight2, gears[2].weight2))

    return viable_combos

# FILTER GEAR COMBINATIONS
def filter_gear_combos(gear_combos):
    '''aaa = []
    for combo in gear_combos:
        if(str(combo.gears[0]) == "35_2" and str(combo.gears[1]) == "60_2"):
            print([str(gear) for gear in combo.gears])
            print(combo.fos)'''

    return [combo for combo in gear_combos if combo.newmass < max_mass and \
        all(min_fos <= x <= max_fos for x in combo.newfos) and \
        combo.length > min_length
        ]

# WRITE NEW CSV OF GOOD GEAR COMBINATIONS
def write_gear_sheet(final_combos):
    with open("Possible Gear Combos", "w") as f:
        w = csv.writer(f)
        # write header row

        header_row = [ 
            "Gear 1", "Mass 1", "PitchD 1", "FOS 1", "Width 1",
            "Gear 2", "Mass 2", "PitchD 2", "FOS 2", "Width 2",
            "Gear 3", "Mass 3", "PitchD 3", "FOS 3", "Width 3",
            "Gear 4", "Mass 4", "PitchD 4", "FOS 4", "Width 4",
            "Total Reduction", "Reduction 1", "Reduction 2",
            "Total Mass", "Center to Center Length"
        ]

        w.writerow(header_row)
        for combo in final_combos:
            w.writerow(combo.info)


test = filter_gear_combos(possible_gear_combos(read_gear_sheet()))

write_gear_sheet(test)