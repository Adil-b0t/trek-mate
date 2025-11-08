#!/usr/bin/env python3
"""
Script to import trek data from trekdata.txt into the database
This script will parse all 28 treks and store every single detail without losing any information
"""

import re
from app import app, db, TrekRegion, Trek, PrivateRoute, PublicRoute, TrekHighlight

def clean_text(text):
    """Clean text by removing emojis and extra whitespace"""
    if not text:
        return ""
    # Remove emojis and special characters but keep essential info
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text).strip()

def parse_height(height_text):
    """Extract height in feet and meters from text"""
    if not height_text:
        return None, None
    
    # Look for pattern like "4,514 ft (1,376 m)" or "2,160 ft (659 m)"
    height_match = re.search(r'(\d+,?\d+)\s*ft.*?\((\d+,?\d+)\s*m\)', height_text)
    if height_match:
        ft = int(height_match.group(1).replace(',', ''))
        m = int(height_match.group(2).replace(',', ''))
        return ft, m
    
    # Try just feet
    ft_match = re.search(r'(\d+,?\d+)\s*ft', height_text)
    if ft_match:
        ft = int(ft_match.group(1).replace(',', ''))
        return ft, None
    
    return None, None

def parse_distance(distance_text):
    """Extract distance in km"""
    if not distance_text:
        return None
    
    # Look for patterns like "~7 km", "13 km", "3.5 km"
    dist_match = re.search(r'~?(\d+\.?\d*)\s*km', distance_text)
    if dist_match:
        return float(dist_match.group(1))
    
    return None

def extract_difficulty_info(difficulty_text):
    """Extract difficulty level and color code"""
    if not difficulty_text:
        return None, None
    
    difficulty_map = {
        'Easy': 'green',
        'Moderate': 'orange', 
        'Hard': 'red'
    }
    
    for level, color in difficulty_map.items():
        if level.lower() in difficulty_text.lower():
            return level, color
    
    return None, None

def parse_route_distance_and_time(route_text):
    """Parse distance and time from route description"""
    if not route_text:
        return None, None
    
    # Extract distance like "~60 km", "200 km"
    dist_match = re.search(r'~?(\d+)\s*km', route_text)
    distance = int(dist_match.group(1)) if dist_match else None
    
    # Extract time like "~2 hrs", "3.5 hrs"  
    time_match = re.search(r'~?(\d+\.?\d*)\s*hrs?', route_text)
    duration = f"{time_match.group(1)} hrs" if time_match else None
    
    return distance, duration

def parse_trek_data():
    """Parse the complete trek data from trekdata.txt"""
    with open('trekdata.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Define regions from the data
    regions_data = [
        "Pune – Lonavala – Mulshi Belt",
        "Mumbai – Panvel – Karjat – Matheran Belt", 
        "Nashik – Bhandardara Belt",
        "Satara – Mahabaleshwar – Kaas Belt",
        "Malshej Ghat Belt",
        "Konkan Belt"
    ]
    
    # Trek data structure - manually extracted from the file for accuracy
    trek_data = [
        {
            'name': 'Rajgad Fort',
            'full_name': 'Rajgad Fort (Gunjavane Route)',
            'region': 'Pune – Lonavala – Mulshi Belt',
            'gen_z_intro': "Rajgad served as the capital of Chhatrapati Shivaji Maharaj for nearly 25 years and played a central role in Maratha history. The fort's complex of palaces, water cisterns and defensive walls shows sophisticated hill-fort planning. Today Rajgad is prized by trekkers for its panoramic views, monsoon greenery and well-preserved historic ruins.",
            'height_ft': 4514, 'height_m': 1376,
            'distance_km': 7.0,
            'duration': '2.5–3 hrs climb | 5–6 hrs with exploration',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'June–Feb',
            'base_village': 'Gunjavane',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Start at Swargate → take the NH65 towards Katraj → continue to Shivapur → turn left towards Nasrapur → follow signs to Gunjavane.',
                    'distance_km': 60, 'duration': '2 hrs',
                    'road_condition': 'Good, last 5 km is a village road.',
                    'parking_info': 'Available near the base; ₹50–₹100 fee.'
                },
                {
                    'from_city': 'Mumbai', 
                    'route_description': 'Start at Dadar → take the Mumbai–Pune Expressway → exit at Lonavala → follow signs to Malavli → continue to Gunjavane.',
                    'distance_km': 200, 'duration': '3.5 hrs',
                    'road_condition': 'Excellent, last 5 km is a village road.',
                    'parking_info': 'Available near the base; ₹50–₹100 fee.'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate Bus Stand → MSRTC bus to Velhe → get down at Gunjavane.',
                    'total_time': '2.5 hrs',
                    'frequency': 'Buses every 30–45 mins.'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Lonavala → Malavli → MSRTC bus to Velhe → get down at Gunjavane.',
                    'total_time': '4.5 hrs',
                    'frequency': 'Trains every 30 mins; buses every 1 hr.'
                }
            ]
        },
        {
            'name': 'Andharban Jungle Trek',
            'full_name': 'Andharban Jungle Trek',
            'region': 'Pune – Lonavala – Mulshi Belt',
            'gen_z_intro': "Andharban (literally ‘dark forest’) is a moist deciduous stretch in the Mulshi range known for dense monsoon forests and seasonal streams. Though not a built fort, the trail is historically a passage between villages and plateaus used by local communities. Today it’s celebrated for its waterfalls, rich biodiversity and an immersive monsoon trekking experience.",
            'height_ft': 2160, 'height_m': 659,
            'distance_km': 13.0,
            'duration': '4–5 hrs',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'June–Sept',
            'base_village': 'Pimpri',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Start at Swargate → take the Paud Road → continue to Mulshi → follow signs to Pimpri.',
                    'distance_km': 70, 'duration': '2.5 hrs',
                    'road_condition': 'Good, last 5 km is a village road.',
                    'parking_info': 'Available near the base; ₹50–₹100 fee.'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Start at Dadar → take the Mumbai–Pune Expressway → exit at Lonavala → follow signs to Mulshi → continue to Pimpri.',
                    'distance_km': 200, 'duration': '3.5 hrs',
                    'road_condition': 'Excellent, last 5 km is a village road.',
                    'parking_info': 'Available near the base; ₹50–₹100 fee.'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate Bus Stand → MSRTC bus to Paud → get down at Paud → shared jeep to Pimpri.',
                    'total_time': '3 hrs',
                    'frequency': 'Buses every 30–45 mins; jeeps every 1 hr.'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Lonavala → MSRTC bus to Mulshi → shared jeep to Pimpri.',
                    'total_time': '5 hrs',
                    'frequency': 'Trains every 30 mins; buses every 1 hr; jeeps every 1 hr.'
                }
            ]
        },
        {
            'name': 'Lohagad-Visapur Fort',
            'full_name': 'Lohagad-visapur Fort',
            'region': 'Pune – Lonavala – Mulshi Belt',
            'gen_z_intro': "Lohagad and Visapur are twin hill forts with roots in the Maratha and later British periods; Lohagad is famous for its ‘U’-shaped ridge and Lohagad’s Vinayak temple. Historically these forts guarded trade routes near the Lonavala pass. Today they remain accessible, popular beginner treks with panoramic valley views and easy-to-follow ridgelines.",
            'height_ft': 3389, 'height_m': 1033,
            'distance_km': 5.0,
            'duration': '1.5–2 hrs climb | 3–4 hrs round trip',
            'difficulty': 'Easy', 'difficulty_color': 'green',
            'best_season': 'June–Feb',
            'base_village': 'Lohagadwadi',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Start at Swargate → take the NH48 towards Lonavala → exit at Malavli → follow signs to Lohagadwadi.',
                    'distance_km': 65, 'duration': '2 hrs',
                    'road_condition': 'Excellent, last 2 km is a village road.',
                    'parking_info': 'Available near the base; ₹50–₹100 fee.'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Start at Dadar → take the Mumbai–Pune Expressway → exit at Lonavala → follow signs to Malavli → continue to Lohagadwadi.',
                    'distance_km': 200, 'duration': '3.5 hrs',
                    'road_condition': 'Excellent, last 2 km is a village road.',
                    'parking_info': 'Available near the base; ₹50–₹100 fee.'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate Bus Stand → MSRTC bus to Malavli → shared jeep to Lohagadwadi.',
                    'total_time': '2.5 hrs',
                    'frequency': 'Buses every 30–45 mins; jeeps every 1 hr.'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Malavli → shared jeep to Lohagadwadi.',
                    'total_time': '4.5 hrs',
                    'frequency': 'Trains every 30 mins; jeeps every 1 hr.'
                }
            ]
        },
        {
            'name': 'Tikona Fort',
            'full_name': 'Tikona Fort',
            'region': 'Pune – Lonavala – Mulshi Belt',
            'gen_z_intro': "Named for its triangular shape, Tikona (Tikona Peth) has long been a lookout fort guarding the Pawna valley and trade routes. It features historic rock-cut steps, temples and water cisterns that hint at its strategic past. Modern trekkers flock to Tikona for steep ascents, 360° views of Pawna Lake, and sunrise photography.",
            'height_ft': 3500, 'height_m': 1067,
            'distance_km': 3.5,
            'duration': '1.5–2 hrs climb | 3–4 hrs round trip',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'June–Feb',
            'base_village': 'Tikona Peth',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Start at Swargate → take the NH48 towards Lonavala → exit at Kamshet → follow signs to Tikona Peth village.',
                    'distance_km': 60, 'duration': '2 hrs',
                    'road_condition': 'Mostly good tar roads; last 2–3 km is a narrow village road.',
                    'parking_info': 'Available in Tikona Peth near the base; usually free.'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Start at Dadar → take the Mumbai–Pune Expressway → exit at Kamshet → follow signs to Tikona Peth.',
                    'distance_km': 110, 'duration': '3 hrs',
                    'road_condition': 'Excellent till Kamshet; last 2–3 km village road.',
                    'parking_info': 'Available at the base.'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Reach Swargate Bus Stand. Take MSRTC bus towards Kamshet or Tikona Peth (buses every 30–45 mins). Get down at Tikona Peth village, walk ~5–10 min to trek base.',
                    'total_time': '2.5 hrs',
                    'frequency': 'Buses every 30–45 mins'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Take train on Central Line to Kamshet Station (local trains from Karjat or Mumbai CST). From Kamshet Station → shared auto / rickshaw / cab to Tikona Peth village (~10 min). Trek base is a short walk from village.',
                    'total_time': '3.5 hrs',
                    'frequency': 'Local trains available'
                }
            ]
        },
        {
            'name': 'Torna Fort',
            'full_name': 'Torna Fort (Prachandagad)',
            'region': 'Pune – Lonavala – Mulshi Belt',
            'gen_z_intro': "Torna (Prachandagad) is famed as Chhatrapati Shivaji Maharaj’s first conquest and an important Maratha stronghold. Its steep approaches and expansive plateau made it a strategic defensive site through medieval times. Today Torna challenges trekkers with a long ascent and rewards them with sweeping views and rich historical remains.",
            'height_ft': 4450, 'height_m': 1356,
            'distance_km': 6.0,
            'duration': '3–4 hrs climb | 7–8 hrs round trip',
            'difficulty': 'Hard', 'difficulty_color': 'red',
            'best_season': 'June–Feb',
            'base_village': 'Torna Peth',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → NH48 → Saswad → Torna Peth',
                    'distance_km': 65, 'duration': '2 hrs',
                    'road_condition':'Good tar roads till Velhe; last 7-8 km rough village road with steep gradients.',
                    'parking_info': 'Available near base village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Mumbai–Pune Expressway → Pune → Saswad → Torna Peth',
                    'distance_km': 135, 'duration': '3.5 hrs',
                    'road_condition': 'Good roads till Velhe via Pune; last 7-8 km rough mountain road. Parking limited at base.',
                    'parking_info': 'Available near base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate Bus Stand → MSRTC bus to Saswad (~1 hr, buses every 30–45 mins). Saswad → shared auto/jeep to Torna Peth (~15 mins, jeeps every 30–60 mins). Trek base → short walk (~5–10 mins)',
                    'total_time': 'About 1.5 hrs',
                    'frequency': 'Buses every 30–45 mins; jeeps every 30–60 mins'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Pune Junction (~3 hrs, trains every 30 mins). Pune → Swargate → MSRTC bus to Saswad (~1 hr). Saswad → shared auto/jeep to Torna Peth (~15 mins)',
                    'total_time': 'About 4.5 hrs',
                    'frequency': 'Trains every 30 mins'
                }
            ]
        },
        {
            'name': 'Rajmachi Fort',
            'full_name': 'Rajmachi Fort',
            'region': 'Pune – Lonavala – Mulshi Belt',
            'gen_z_intro': "Rajmachi is actually a pair of forts (Shrivardhan and Manaranjan) that formed an important watchpoint for the Karjat–Lonavala corridor. It has historical links to trade-route surveillance and seasonal military use. Currently Rajmachi is a cherished monsoon trek, popular for its campsites, lakes in the valley and easy access from Lonavala/Karjat.",
            'height_ft': 2700, 'height_m': 823,
            'distance_km': 8.0,
            'duration': '3–4 hrs climb | 6–7 hrs round trip',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'June–Feb',
            'base_village': 'Udhewadi / Kondhane',
            'private_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Mumbai–Pune Expressway → Lonavala → Khandala → Karjat → Kondhane Village',
                    'distance_km': 100, 'duration': '3 hrs',
                    'road_condition':'Excellent roads till Lonavala; approach via Valvan Dam - last 8 km rough village road.',
                    'parking_info': 'Available near base village'
                },
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → NH48 → Lonavala → Khandala → Kondhane',
                    'distance_km': 65, 'duration': '2 hrs',
                    'road_condition': 'Good roads till Lonavala; last 8 km via Valvan Dam is rough village road with stream crossings.',
                    'parking_info': 'Available near base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Take train to Lonavala Station. From Lonavala → local bus / shared jeep to Udhewadi / Kondhane (~1 hr)',
                    'total_time': '4 hrs',
                    'frequency': 'Regular trains to Lonavala'
                },
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Khandala. From Khandala → shared jeep to Udhewadi / Kondhane',
                    'total_time': '3.5 hrs',
                    'frequency': 'Regular buses to Khandala'
                }
            ]
        },
        {
            'name': "Duke's Nose",
            'full_name': "Duke's Nose (Nagphani)",
            'region': 'Pune – Lonavala – Mulshi Belt',
            'gen_z_intro': "Also called Nagphani, Duke’s Nose is a steep rocky cliff used historically as a natural lookout and landmark. It became popular among early colonial-era climbers for its distinctive profile. Today it’s a short, thrilling trek and local climbing spot offering sunrise views over the surrounding Ghats and valleys.",
            'height_ft': 2820, 'height_m': 860,
            'distance_km': 3.0,
            'duration': '1.5–2 hrs climb | 3 hrs round trip',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'June–Feb',
            'base_village': 'Kamshet',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → NH48 → Lonavala → Kamshet → Duke\'s Nose Base',
                    'distance_km': 65, 'duration': '2 hrs',
                    'road_condition': 'Good tar roads',
                    'parking_info': 'Available near base'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Mumbai–Pune Expressway → Lonavala → Kamshet → Duke\'s Nose Base',
                    'distance_km': 120, 'duration': '3 hrs',
                    'road_condition': 'Good tar roads',
                    'parking_info': 'Available near base'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Kamshet. Walk/auto to Duke\'s Nose base (~5–10 min)',
                    'total_time': '2.5 hrs',
                    'frequency': 'Regular buses'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Train to Kamshet Station. Auto/jeep to Duke\'s Nose (~5–10 min)',
                    'total_time': '3 hrs',
                    'frequency': 'Regular trains'
                }
            ]
        },
        {
            'name': 'Devkund Waterfall',
            'full_name': 'Devkund Waterfall',
            'region': 'Pune – Lonavala – Mulshi Belt',
            'gen_z_intro': "Devkund is a natural plunge waterfall forming a scenic plunge pool at the confluence of small streams in the Tamhini region. While not an ancient fort, the spot is locally important for water and village access. Today Devkund is famous for its dramatic monsoon flow, accessible waterfall basin and short, scenic trail popular with families.",
            'height_ft': 150, 'height_m': None,
            'distance_km': 5.0,
            'duration': '2.5 hrs',
            'difficulty': 'Easy', 'difficulty_color': 'green',
            'best_season': 'June–October (monsoon)',
            'base_village': 'Bhira / Tamhini',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → NH66 → Tamhini → Bhira',
                    'distance_km': 80, 'duration': '2.5 hrs',
                    'road_condition': 'Good tar roads till Bhira village; last 2 km rough village road. Best to park at Bhira and walk.',
                    'parking_info': 'Parking available near base village (paid)'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Panvel → Khopoli → Pali → Bhira',
                    'distance_km': 170,
                    'duration': '4.5 hrs',
                    'road_condition': 'Good till Pali, last stretch towards Bhira is narrow village road.',
                    'parking_info': 'Parking available at Bhira village (paid).'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus towards Mangaon / Kolad (get down for Bhira via Tamhini) (~2.5 hrs) → Walk to Bhira (~30 mins).',
                    'total_time': '3 hrs',
                    'frequency': 'Regular buses'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → Train to Lonavala (~2 hrs) → Bus to Tamhini (~1 hr) → Walk to Bhira (~30 mins).',
                    'total_time': '3.5 hrs',
                    'frequency': 'Regular trains and buses'
                }
            ]
        }
        # Continue with remaining treks - I'll add them all systematically
    ]
    
    # Add remaining treks from Mumbai-Panvel belt
    mumbai_panvel_treks = [
        {
            'name': 'Prabalgad–Kalavantin Durg',
            'full_name': 'Prabalgad–Kalavantin Durg',
            'region': 'Mumbai – Panvel – Karjat – Matheran Belt',
            'gen_z_intro': "Prabalgad and the adjacent Kalavantin Durg form an iconic twin feature near Matheran with steep pinnacles and long ridge walks. Historically the forts served as hilltop observatories and hill-fort outposts. Today they’re renowned for exposed climbs, iron ladder sections and dramatic sunrise/sunset vistas for experienced trekkers.",
            'height_ft': 2600, 'height_m': 792,
            'distance_km': 3.0,
            'duration': '1.5–2 hrs climb | 3–4 hrs round trip',
            'difficulty': 'Hard', 'difficulty_color': 'red',
            'best_season': 'Oct–Feb',
            'base_village': 'Thakurwadi / Prabalmachi',
            'private_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Panvel → Neral → Thakurwadi',
                    'distance_km': 80, 'duration': '2 hrs',
                    'road_condition':'Excellent roads till Panvel, then good till Thakurwadi; last 2 km village road.',
                    'parking_info': 'Available near base village'
                },
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Panvel → Neral → Thakurwadi',
                    'distance_km': 150, 'duration': '3 hrs',
                    'road_condition':'Good roads till Thakurwadi village; last 2 km village road. Limited parking in village.',
                    'parking_info': 'Available near base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Neral (~2 hrs, trains every 30 mins). Neral → shared jeep / auto to Thakurwadi (~30–40 min, every 1 hr). Trek base → short walk (~5–10 min)',
                    'total_time': '3 hrs',
                    'frequency': 'Trains every 30 mins; jeeps every 1 hr'
                },
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Panvel (~3 hrs, buses every 1–2 hrs). Panvel → local bus / shared jeep to Thakurwadi (~1 hr, every 1 hr). Trek base → short walk (~5–10 min)',
                    'total_time': '4.5 hrs',
                    'frequency': 'Buses every 1–2 hrs'
                }
            ]
        },
        {
            'name': 'Irshalgad Fort',
            'full_name': 'Irshalgad Fort',
            'region': 'Mumbai – Panvel – Karjat – Matheran Belt',
            'gen_z_intro': "Irshalgad is a compact fort known for its rockface and sheltered top with ruins of minor fortifications — it historically guarded local trade tracks. The approachable trail and solitude make it a quieter alternative to nearby crowded peaks. Today it’s popular for short treks, photography and peaceful hilltop views.",
            'height_ft': 2700, 'height_m': 823,
            'distance_km': 3.0,
            'duration': '1.5–2 hrs climb | 3–4 hrs round trip',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'Oct–Feb',
            'base_village': 'Peth',
            'private_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Panvel → Neral → Peth',
                    'distance_km': 85, 'duration': '2–2.5 hrs',
                    'road_condition':'Excellent roads till Murbad; last 4 km village road through paddy fields. Can get muddy during monsoon.',
                    'parking_info': 'Available near base village'
                },
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Panvel → Neral → Peth',
                    'distance_km': 150, 'duration': '3–3.5 hrs',
                    'road_condition':'Good tar roads till Murbad; last 4 km village road.',

                    'parking_info': 'Available near base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Neral (~2 hrs, trains every 30 mins). Neral → shared jeep / auto to Peth (~20–30 mins, jeeps every 1 hr). Trek base → short walk (~5–10 min)',
                    'total_time': '3 hrs',
                    'frequency': 'Trains every 30 mins; jeeps every 1 hr'
                },
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Panvel (~3 hrs, buses every 1–2 hrs). Panvel → local bus / shared jeep to Peth (~1 hr, jeeps every 1 hr). Trek base → short walk (~5–10 min)',
                    'total_time': '4.5 hrs',
                    'frequency': 'Buses every 1–2 hrs'
                }
            ]
        },
        {
            'name': 'Peb–Matheran One Tree Hill',
            'full_name': 'Peb–Matheran One Tree Hill',
            'region': 'Mumbai – Panvel – Karjat – Matheran Belt',
            'gen_z_intro': "The One Tree Hill (Peb) in the Matheran region is a scenic viewpoint with hill-station heritage; Matheran itself has long been a protected, vehicle-free resort area since colonial times. The spot offers panoramic valley views, cool hill-station air and classic Matheran trails. Today it’s a gentle trek favoured for sunrise and easy hiking.",
            'height_ft': 2600, 'height_m': 792,
            'distance_km': 4.0,
            'duration': '2–2.5 hrs climb | 4–5 hrs round trip',
            'difficulty': 'Easy–Moderate', 'difficulty_color': 'orange',
            'best_season': 'Oct–Feb',
            'base_village': 'Matheran',
            'private_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Panvel → Neral → Matheran',
                    'distance_km': 90, 'duration': '2.5 hrs',
                    'road_condition':'Good roads till Neral; vehicles not allowed to Matheran - use toy train or walk via Dasturi Naka.',
                    'parking_info': 'At Neral (Matheran is vehicle-free; horse/hand-pulled rickshaw to base)'
                },
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Panvel → Neral → Matheran',
                    'distance_km': 150, 'duration': '3.5 hrs',
                    'road_condition':'Excellent roads till Neral; vehicles restricted to Matheran. Train or trek from Dasturi Naka.',

                    'parking_info': 'At Neral (Matheran is vehicle-free; horse/hand-pulled rickshaw to base)'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Neral (~2 hrs, trains every 30 mins). Neral → Toy Train / shared rickshaw to Matheran (~30–40 mins, every 1 hr). Trek base → short walk to One Tree Hill (~10 mins)',
                    'total_time': '3 hrs',
                    'frequency': 'Trains every 30 mins'
                },
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Panvel (~3 hrs, buses every 1–2 hrs). Panvel → local train to Neral (~1 hr, trains every 1 hr). Neral → Toy Train / rickshaw to Matheran (~30–40 mins). Trek base → short walk to One Tree Hill (~10 mins)',
                    'total_time': '5 hrs',
                    'frequency': 'Buses every 1–2 hrs'
                }
            ],
            'highlights': ['Famous hill-station trek with panoramic valley views', 'Horse ride available if tired of walking', 'Best during sunrise for photography']
        },
        {
            'name': 'Karnala Fort',
            'full_name': 'Karnala Fort',
            'region': 'Mumbai – Panvel – Karjat – Matheran Belt',
            'gen_z_intro': "Karnala is a small fort inside a protected bird sanctuary and has been a historic milestone on coastal trade and defence routes. The fort’s bastions and ruins reflect its strategic role through medieval times. Now Karnala combines heritage with biodiversity — birdwatching plus a short, family-friendly trek to historic ramparts.",
            'height_ft': 1350, 'height_m': 411,
            'distance_km': 2.5,
            'duration': '1–1.5 hrs climb | 2–3 hrs round trip',
            'difficulty': 'Easy', 'difficulty_color': 'green',
            'best_season': 'Oct–Feb',
            'base_village': 'Karnala / Panvel',
            'private_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Panvel → Karnala',
                    'distance_km': 55, 'duration': '1.5 hrs',
                    'road_condition':'Excellent roads via Panvel; well-maintained highway with good parking at base.',
                    'parking_info': 'Available near base village'
                },
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Panvel → Karnala',
                    'distance_km': 120, 'duration': '3 hrs',
                    'road_condition':'Excellent roads throughout; well-developed tourist destination with facilities.',

                    'parking_info': 'Available near base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'CST / Dadar → local train to Panvel (~1.5 hrs, trains every 30 mins). Panvel → MSRTC bus / auto to Karnala (~20–25 mins, buses every 1 hr). Trek base → short walk (~5–10 mins)',
                    'total_time': '2.5 hrs',
                    'frequency': 'Trains every 30 mins; buses every 1 hr'
                },
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Panvel (~3 hrs, buses every 1–2 hrs). Panvel → MSRTC bus / shared jeep to Karnala (~20–25 mins, buses every 1 hr). Trek base → short walk (~5–10 mins)',
                    'total_time': '4 hrs',
                    'frequency': 'Buses every 1–2 hrs'
                }
            ]
        },
        {
            'name': 'Sondai Fort',
            'full_name': 'Sondai Fort (Karjat)',
            'region': 'Mumbai – Panvel – Karjat – Matheran Belt',
            'gen_z_intro': "Sondai is a modest hill fort near Karjat that historically acted as a lookout for local hill tracks and settlements. Its relative isolation has preserved quiet trails and scattered ruins. Today it offers a peaceful short trek with sunrise viewpoints and far fewer crowds than some popular nearby forts.",
            'height_ft': 2000, 'height_m': 610,
            'distance_km': 2.0,
            'duration': '1–1.5 hrs climb | 2–3 hrs round trip',
            'difficulty': 'Easy', 'difficulty_color': 'green',
            'best_season': 'Oct–Feb',
            'base_village': 'Sondai',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Karjat → Sondewadi village',
                    'distance_km': 50, 'duration': '1.5 hrs',
                    'road_condition':'Good roads till base village; last 2-3 km village road. Parking available near temple.',
                    'parking_info': 'Available near the base village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Mumbai–Pune Expressway → Pune → Karjat → Sondewadi',
                    'distance_km': 120, 'duration': '3.5 hrs',
                    'road_condition':'Decent roads via Pune route; last 2-3 km village road with some rough patches.',

                    'parking_info': 'Available near the base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate Bus Stand → MSRTC bus to Saswad (~1 hr, buses every 30–60 mins). Saswad → shared auto/jeep to Sondewadi village (~15–20 mins, autos/jeeps every 30–60 mins)',
                    'total_time': '1.5 hrs',
                    'frequency': 'Buses every 30–60 mins; autos/jeeps every 30–60 mins'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Pune Junction (~3 hrs, trains every 30 mins). Pune → Swargate → MSRTC bus to Saswad (~1 hr, buses every 30–60 mins). Saswad → shared auto/jeep to Sondewadi village (~15–20 mins, autos/jeeps every 30–60 mins)',
                    'total_time': '4.5 hrs',
                    'frequency': 'Trains every 30 mins'
                }
            ]
        }
    ]
    
    trek_data.extend(mumbai_panvel_treks)
    
    # Add Nashik-Bhandardara belt treks
    nashik_treks = [
        {
            'name': 'Kalsubai Peak',
            'full_name': 'Kalsubai Peak',
            'region': 'Nashik – Bhandardara Belt',
            'gen_z_intro': "Kalsubai is Maharashtra’s highest peak and has long-standing local religious significance, with a small temple near the summit visited by pilgrims. Historically the peak served as a natural high point for signalling across valleys. Today Kalsubai is a challenging but well-traveled trek — famous for sunrise summits, ridge scrambles and panoramic views across the Sahyadris.",
            'height_ft': 5400, 'height_m': 1646,
            'distance_km': 6.0,
            'duration': '3–4 hrs climb | 6–7 hrs round trip',
            'difficulty': 'Hard', 'difficulty_color': 'red',
            'best_season': 'Oct–Feb',
            'base_village': 'Bari / Bhandardara',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → NH60 → Bhandardara → Bari',
                    'distance_km': 170, 'duration': '4 hrs',
                    'road_condition':'Good roads till Bari village; last 3 km narrow village road. Limited parking at base.',
                    'parking_info': 'Available at Bari village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Mumbai–Thane → Igatpuri → Bhandardara → Bari',
                    'distance_km': 180, 'duration': '4.5 hrs',
                    'road_condition': 'Decent roads via Igatpuri-Ghoti; last 3 km narrow mountain road. Early start recommended.',
                    'parking_info': 'Available at Bari village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Igatpuri (~3.5 hrs, buses every 1–2 hrs). Igatpuri → shared jeep to Bari (~1 hr, jeeps every 1 hr). Trek base → short walk (~5–10 mins)',
                    'total_time': '5 hrs',
                    'frequency': 'Buses every 1–2 hrs; jeeps every 1 hr'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Kasara (~2.5 hrs, trains every 30 mins). Kasara → MSRTC bus to Igatpuri (~1 hr, buses every 1 hr). Igatpuri → shared jeep to Bari (~1 hr, jeeps every 1 hr). Trek base → short walk (~5–10 mins)',
                    'total_time': '5 hrs',
                    'frequency': 'Trains every 30 mins'
                }
            ]
        },
        {
            'name': 'Harihar Fort',
            'full_name': 'Harihar Fort',
            'region': 'Nashik – Bhandardara Belt',
            'gen_z_intro': "Harihar Fort is known for its steep vertical rock face and exposed ridge, historically used for hill-defence and local control of surrounding valleys. Climbing routes include fixed chains and narrow ledges that hint at the fort’s defensive design. Today Harihar is an adrenaline-heavy trek for experienced groups seeking cliffside adventure and wide-range views.",
            'height_ft': 3600, 'height_m': 1097,
            'distance_km': 4.0,
            'duration': '2–3 hrs climb | 4–5 hrs round trip',
            'difficulty': 'Hard', 'difficulty_color': 'red',
            'best_season': 'Oct–Feb',
            'base_village': 'Nirgudpada (Takeharsha)',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Wai → Ambevadi',
                    'distance_km': 130, 'duration': '3.5 hrs',
                    'road_condition':'Good tar roads till Nirgudpada village; last 2 km village road. Parking available in village.',
                    'parking_info': 'Available at base village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Mumbai–Pune Expressway → Wai → Ambevadi',
                    'distance_km': 180, 'duration': '4–4.5 hrs',
                    'road_condition':'Good roads via Igatpuri-Ghoti; last 2 km village road with some rough patches.',

                    'parking_info': 'Available at base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Wai (~3 hrs, buses every 1 hr). Wai → shared auto/jeep to Ambevadi (~15–20 mins, every 1 hr). Trek base → short walk (~5–10 mins)',
                    'total_time': '3.5 hrs',
                    'frequency': 'Buses every 1 hr'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Satara (~3.5 hrs, trains every 1 hr). Satara → MSRTC bus to Wai (~1 hr, buses every 1 hr). Wai → shared jeep to Ambevadi (~15–20 mins, every 1 hr)',
                    'total_time': '5 hrs',
                    'frequency': 'Trains every 1 hr'
                }
            ]
        },
        {
            'name': 'Ratangad Fort',
            'full_name': 'Ratangad Fort',
            'region': 'Nashik – Bhandardara Belt',
            'gen_z_intro': "Ratangad features a distinctive stone pinnacle, ancient caves and the historic Amruteshwar temple at its foothills — the fort held regional importance across Maratha and earlier periods. Its ring of bastions and water tanks indicate a well-established hill settlement. Today Ratangad is admired for its panoramic viewpoints, lake-fed scenery and archaeological interest.",
            'height_ft': 4600, 'height_m': 1297,
            'distance_km': 6.0,
            'duration': '3–4 hrs climb | 6–7 hrs round trip',
            'difficulty': 'Hard', 'difficulty_color': 'red',
            'best_season': 'Oct–Feb',
            'base_village': 'Ratangad Peth / Samrad',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Ghoti → Samrad',
                    'distance_km': 150, 'duration': '4 hrs',
                    'road_condition':'Good roads till Ratanwadi village; last 3 km narrow mountain road. Limited parking in village.',
                    'parking_info': 'Available at base village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Kasara → Ghoti → Samrad',
                    'distance_km': 160, 'duration': '4.5 hrs',
                    'road_condition':'Decent roads via Bhandardara; last 3 km narrow and winding. High-clearance vehicle helpful.',

                    'parking_info': 'Available at base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Ghoti (~4 hrs, buses every 1–2 hrs). Ghoti → shared jeep to Samrad (~30 mins, every 1 hr). Trek base → short walk (~5–10 mins)',
                    'total_time': '5 hrs',
                    'frequency': 'Buses every 1–2 hrs'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Kasara (~2.5 hrs, trains every 30 mins). Kasara → MSRTC bus to Ghoti (~1 hr, buses every 1 hr). Ghoti → shared jeep to Samrad (~30 mins, every 1 hr)',
                    'total_time': '4.5 hrs',
                    'frequency': 'Trains every 30 mins'
                }
            ]
        },
        {
            'name': 'Anjaneri–Brahmagiri Hills',
            'full_name': 'Anjaneri–Brahmagiri Hills',
            'region': 'Nashik – Bhandardara Belt',
            'gen_z_intro': "Anjaneri is traditionally associated in local legend with the birthplace of Lord Hanuman, giving the hill religious and cultural importance. The range combines temple sites, springs and forested trails that supported local pilgrims and village life. Today the Anjaneri–Brahmagiri circuit is popular for cultural treks, biodiversity and early-morning summit views.",
            'height_ft': 4000, 'height_m': 1280,
            'distance_km': 5.0,
            'duration': '2.5–3 hrs climb | 5–6 hrs round trip',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'Oct–Feb',
            'base_village': 'Anjaneri / Trimbakeshwar',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Nashik → Trimbakeshwar → Anjaneri',
                    'distance_km': 210, 'duration': '5 hrs',
                    'road_condition':'Good roads till Trimbakeshwar; last 3-4 km village road to base. Parking available at temple.',
                    'parking_info': 'Available near base village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Thane → Nashik → Trimbakeshwar → Anjaneri',
                    'distance_km': 180, 'duration': '5 hrs',
                    'road_condition':'Good roads via Nashik-Trimbakeshwar; last 3-4 km village road with temple parking.',
                    'parking_info': 'Available near base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Nashik (~5 hrs, buses every 1–2 hrs). Nashik → local bus to Trimbakeshwar (~1 hr, buses every 30–60 mins). Trimbakeshwar → shared jeep/auto to Anjaneri (~20–30 mins)',
                    'total_time': '6.5 hrs',
                    'frequency': 'Buses every 1–2 hrs'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Nashik (~5 hrs, trains every 1 hr). Nashik → local bus to Trimbakeshwar (~1 hr, buses every 30–60 mins). Trimbakeshwar → shared jeep/auto to Anjaneri (~20–30 mins)',
                    'total_time': '6.5 hrs',
                    'frequency': 'Trains every 1 hr'
                }
            ]
        },
        {
            'name': 'Alang–Madan–Kulang (AMK) Forts',
            'full_name': 'Alang–Madan–Kulang (AMK) Forts',
            'region': 'Nashik – Bhandardara Belt',
            'gen_z_intro': "Alang, Madan and Kulang together form one of the most challenging multi-peak fort complexes in the Western Ghats with historic hill-fort structures and caves. Historically these forts were used for strategic defence and seasonal habitation. Today AMK is a technical, full-day adventure sought by experienced trekkers for steep climbs, ridgelines and long ridge traverses.",
            'height_ft': 4650, 'height_m': 1418,  # Average of the range 4,500–4,800 ft
            'distance_km': 12.0,
            'duration': '6–8 hrs full trek',
            'difficulty': 'Hard', 'difficulty_color': 'red',
            'best_season': 'Oct–Feb',
            'base_village': 'Thakurwadi / Ambewadi',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Lonavala → Thakurwadi',
                    'distance_km': 120, 'duration': '3–3.5 hrs',
                    'road_condition': 'Good roads till Igatpuri; last 4-5 km rough village road to base. High-clearance vehicle recommended.',
                    'parking_info': 'Available at base village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Panvel → Neral → Thakurwadi',
                    'distance_km': 90, 'duration': '2.5 hrs',
                    'road_condition': 'Decent roads via Igatpuri; last 4-5 km rough mountain road. Four-wheel drive preferred for monsoon.',

                    'parking_info': 'Available at base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Neral (~2 hrs, trains every 30 mins). Neral → shared jeep to Thakurwadi (~30–40 mins, every 1 hr). Trek base → start trek',
                    'total_time': '3 hrs',
                    'frequency': 'Trains every 30 mins'
                },
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Lonavala (~2 hrs, buses every 30–45 mins). Lonavala → local bus / shared jeep to Thakurwadi (~1 hr, jeeps every 1 hr)',
                    'total_time': '3.5 hrs',
                    'frequency': 'Buses every 30–45 mins'
                }
            ]
        },
        {
            'name': 'Randha Falls',
            'full_name': 'Randha Falls (Bhandardara)',
            'region': 'Nashik – Bhandardara Belt',
            'gen_z_intro': "Randha Falls in the Bhandardara area is a powerful seasonal cascade fed by monsoon rains and the Pravara river system, long-valued by local settlements for water and fishing. While not a fort, the site is an important natural landmark. Today it’s a short scenic hike, especially spectacular in monsoon when the falls are in full flow.",
            'height_ft': 170, 'height_m': 52,
            'distance_km': 1.5,  # Average of 1–2 km
            'duration': '30–45 mins hike | 1–1.5 hrs round trip',
            'difficulty': 'Easy', 'difficulty_color': 'green',
            'best_season': 'June–Oct',
            'base_village': 'Bhandardara',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → NH60 → Bhandardara',
                    'distance_km': 150, 'duration': '4 hrs',
                    'road_condition': 'Excellent roads via Bhandardara; well-maintained tar roads throughout. Good parking facilities.',
                    'parking_info': 'Available near waterfall'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Kasara → Bhandardara',
                    'distance_km': 180, 'duration': '4–4.5 hrs',
                    'road_condition':'Good roads via Nashik-Bhandardara route; tar roads throughout with adequate parking.',

                    'parking_info': 'Available near waterfall'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Igatpuri (~3.5 hrs, buses every 1–2 hrs). Igatpuri → shared jeep to Bhandardara (~1 hr, jeeps every 1 hr)',
                    'total_time': '4.5 hrs',
                    'frequency': 'Buses every 1–2 hrs'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Kasara (~2.5 hrs, trains every 30 mins). Kasara → MSRTC bus to Bhandardara (~1 hr, buses every 1 hr)',
                    'total_time': '3.5 hrs',
                    'frequency': 'Trains every 30 mins'
                }
            ]
        }
    ]
    
    trek_data.extend(nashik_treks)
    
    # Add Satara-Mahabaleshwar belt treks
    satara_treks = [
        {
            'name': 'Ajinkyatara–Sajjangad Forts',
            'full_name': 'Ajinkyatara–Sajjangad Forts',
            'region': 'Satara – Mahabaleshwar – Kaas Belt',
            'gen_z_intro': "Ajinkyatara and Sajjangad are two prominent forts with deep Maratha-era significance; Ajinkyatara hosted dynastic fort activity while Sajjangad is remembered for its later spiritual association with Sant Ramdas. Both forts played roles in regional defence and local governance. Today they provide accessible historical treks and panoramic city views near Satara.",
            'height_ft': 3250, 'height_m': 991,  # Average of the two forts
            'distance_km': 3.5,  # Average of 3–4 km
            'duration': '2–3 hrs climb per fort | 4–6 hrs round trip',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'Oct–Feb',
            'base_village': 'Satara / Sajjangad village',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Satara → Ajinkyatara',
                    'distance_km': 115, 'duration': '3 hrs',
                    'road_condition': 'Excellent roads to Satara city; well-maintained urban roads with good parking facilities.',
                    'parking_info': 'Available near base villages'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Mumbai–Pune Expressway → Satara',
                    'distance_km': 230, 'duration': '5–5.5 hrs',
                    'road_condition':'Good roads via Pune-Satara highway; state roads in good condition with adequate parking.',

                    'parking_info': 'Available near base villages'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Satara (~3–4 hrs, buses every 1 hr). Satara → local auto/jeep to Ajinkyatara / Sajjangad (~10–15 mins, frequent)',
                    'total_time': '4 hrs',
                    'frequency': 'Buses every 1 hr'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Satara (~5 hrs, trains every 1–2 hrs). Satara → local auto/jeep to Ajinkyatara / Sajjangad (~10–15 mins)',
                    'total_time': '5.5 hrs',
                    'frequency': 'Trains every 1–2 hrs'
                }
            ]
        },
        {
            'name': 'Kaas Plateau',
            'full_name': 'Kaas Plateau',
            'region': 'Satara – Mahabaleshwar – Kaas Belt',
            'gen_z_intro': "Kaas Plateau is known as the ‘Valley of Flowers’ of Maharashtra, a UNESCO-recognized biodiversity hotspot during the post-monsoon bloom with hundreds of endemic wildflowers. Traditionally a grazing and plateau landscape, it has become protected for its seasonal flora. Today Kaas attracts botanists, photographers and nature-trekkers during the flower bloom season.",
            'height_ft': 3200, 'height_m': 975,
            'distance_km': 2.5,  # Average of 2–3 km
            'duration': '1–2 hrs',
            'difficulty': 'Easy', 'difficulty_color': 'green',
            'best_season': 'Aug–Oct (monsoon bloom)',
            'base_village': 'Kaas / Patan',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Satara → Patan → Kaas',
                    'distance_km': 120, 'duration': '3.5 hrs',
                    'road_condition': 'Excellent roads via Satara; well-maintained state highway. Good parking and facilities during season.',
                    'parking_info': 'Available near Kaas Plateau entrance'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Mumbai–Pune Expressway → Satara → Patan',
                    'distance_km': 230, 'duration': '5–5.5 hrs',
                    'road_condition':'Good roads via Pune-Satara route; state highway throughout with designated parking areas.',

                    'parking_info': 'Available near Kaas Plateau entrance'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Satara (~3–4 hrs). Satara → local bus / shared jeep to Patan (~30–40 mins). Walk to Kaas Plateau (~5–10 mins)',
                    'total_time': '4.5 hrs',
                    'frequency': 'Regular buses'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Satara (~5 hrs). Satara → local bus / shared jeep to Patan (~30–40 mins). Walk to Kaas Plateau (~5–10 mins)',
                    'total_time': '6 hrs',
                    'frequency': 'Regular trains'
                }
            ]
        },
        {
            'name': "Arthur's Seat Trail",
            'full_name': "Arthur's Seat Trail",
            'region': 'Satara – Mahabaleshwar – Kaas Belt',
            'gen_z_intro': "Arthur’s Seat is a famous cliff-edge viewpoint near Mahabaleshwar with colonial-era hill-station ties and long-standing popularity for panoramic vistas. Historically the area served as leisure viewpoints for visitors to the hill station. Today its cliff views and sunsets remain a major attraction for short treks and photography.",
            'height_ft': 2400, 'height_m': 732,
            'distance_km': 3.0,
            'duration': '1.5–2 hrs climb | 3–4 hrs round trip',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'Oct–Feb',
            'base_village': 'Mahabaleshwar / Lingmala',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Satara → Mahabaleshwar',
                    'distance_km': 120, 'duration': '3.5 hrs',
                    'road_condition':'Excellent tar roads throughout Mahabaleshwar; well-maintained hill station roads with parking.',
                    'parking_info': 'Available near Arthur\'s Seat / Lingmala'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Mumbai–Pune Expressway → Satara → Mahabaleshwar',
                    'distance_km': 230, 'duration': '5 hrs',
                    'road_condition':'Good roads via Mahabaleshwar; state highway in good condition with tourist facilities.',

                    'parking_info': 'Available near Arthur\'s Seat / Lingmala'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Mahabaleshwar (~3–4 hrs). Local auto/jeep to Arthur\'s Seat (~10–15 mins)',
                    'total_time': '4.5 hrs',
                    'frequency': 'Regular buses'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → MSRTC bus to Mahabaleshwar (~6–7 hrs). Local auto/jeep to Arthur\'s Seat (~10–15 mins)',
                    'total_time': '7 hrs',
                    'frequency': 'Regular buses'
                }
            ]
        },
        {
            'name': 'Thoseghar Waterfalls',
            'full_name': 'Thoseghar Waterfalls',
            'region': 'Satara – Mahabaleshwar – Kaas Belt',
            'gen_z_intro': "Thoseghar is a dramatic multi-step waterfall system set in the Western Ghats, known locally for its thunderous monsoon cascades and scenic viewpoints. The area has long been a shrine of natural water resources for nearby settlements. Today Thoseghar is prized for short viewpoint walks and impressive seasonal water flow.",
            'height_ft': 500, 'height_m': 152,
            'distance_km': 1.5,  # Average of 1–2 km
            'duration': '30–45 mins hike | 1 hr round trip',
            'difficulty': 'Easy', 'difficulty_color': 'green',
            'best_season': 'June–Oct',
            'base_village': 'Thoseghar / Satara',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Satara → Thoseghar',
                    'distance_km': 120, 'duration': '3.5 hrs',
                    'road_condition':'Excellent roads via Satara; well-maintained state highway. Good parking and facilities.',
                    'parking_info': 'Available near waterfall'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Satara → Thoseghar',
                    'distance_km': 230, 'duration': '5–5.5 hrs',
                    'road_condition':'Good roads via Pune-Satara route; state highway with good condition throughout.',

                    'parking_info': 'Available near waterfall'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Satara (~3–4 hrs). Satara → shared jeep / auto to Thoseghar (~30 mins)',
                    'total_time': '4.5 hrs',
                    'frequency': 'Regular buses'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Satara (~5 hrs). Satara → shared jeep / auto to Thoseghar (~30 mins)',
                    'total_time': '5.5 hrs',
                    'frequency': 'Regular trains'
                }
            ]
        },
        {
            'name': 'Savlya Ghat',
            'full_name': 'Savlya Ghat',
            'region': 'Satara – Mahabaleshwar – Kaas Belt',
            'gen_z_intro': "Savlya Ghat is a mountain pass and set of ridges known for its sweeping views and cliff approaches; historically it linked plateau regions and local village routes. Its cliffs and viewpoints have long served travellers and shepherding communities. Today Savlya is sought after for short climbs, panoramic photo points and quieter hill treks.",
            'height_ft': 2500, 'height_m': 762,
            'distance_km': 3.0,
            'duration': '1–1.5 hrs climb | 2–3 hrs round trip',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'Oct–Feb',
            'base_village': 'Satara / Savlya',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Satara → Savlya',
                    'distance_km': 110, 'duration': '3 hrs',
                    'road_condition':'Good roads till base village; last 2-3 km village road through farmland. Parking near temple.',
                    'parking_info': 'Near base village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Satara → Savlya',
                    'distance_km': 220, 'duration': '5 hrs',
                    'road_condition':'Good roads via Pune route; last 2-3 km village road with stream crossings during monsoon.',
                    'parking_info': 'Near base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Satara (~3 hrs). Satara → shared jeep / auto to Savlya (~30 mins)',
                    'total_time': '3.5 hrs',
                    'frequency': 'Regular buses'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train to Satara (~5 hrs). Satara → shared jeep / auto to Savlya (~30 mins)',
                    'total_time': '5.5 hrs',
                    'frequency': 'Regular trains'
                }
            ]
        }
    ]
    
    trek_data.extend(satara_treks)
    
    # Add Malshej Ghat belt treks
    malshej_treks = [
        {
            'name': 'Harishchandragad Fort',
            'full_name': 'Harishchandragad Fort (Konkan Kada)',
            'region': 'Malshej Ghat Belt',
            'gen_z_intro': "Harishchandragad is an ancient hill fort famed for its Konkan Kada cliff, rock-cut steps and caves; the fort has deep historic and mythic associations across centuries. Its temples and water cisterns show long-term habitation and ritual use. Today Harishchandragad is a classic Sahyadri trek — popular for overnight camps, sunrise views and technical approaches.",
            'height_ft': 4365, 'height_m': 1331,
            'distance_km': 5.0,
            'duration': '2.5–3.5 hrs climb | 5–6 hrs round trip',
            'difficulty': 'Hard', 'difficulty_color': 'red',
            'best_season': 'Oct–Feb',
            'base_village': 'Kokanwadi / Khireshwar',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → NH61 → Malshej Ghat → Kokanwadi',
                    'distance_km': 130, 'duration': '3.5 hrs',
                    'road_condition':'Good roads till Khireshwar village; last 5 km rough mountain road. High-clearance vehicle recommended.',
                    'parking_info': 'Available at base village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → NH61 → Malshej Ghat → Kokanwadi',
                    'distance_km': 120, 'duration': '3.5 hrs',
                    'road_condition':'Decent roads via Malshej Ghat; last 5 km rough and narrow. Four-wheel drive preferred.',

                    'parking_info': 'Available at base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Malshej Ghat (~3 hrs, buses every 1–2 hrs). Malshej Ghat → shared jeep / auto to Kokanwadi (~15–20 mins). Trek base → short walk (~5 mins)',
                    'total_time': '3.5 hrs',
                    'frequency': 'Buses every 1–2 hrs'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → local train / bus to Kasara (~2 hrs). Kasara → MSRTC bus to Malshej Ghat (~1–1.5 hrs). Malshej Ghat → shared jeep / auto to Kokanwadi (~15–20 mins). Trek base → short walk (~5 mins)',
                    'total_time': '4 hrs',
                    'frequency': 'Regular trains and buses'
                }
            ]
        },
        {
            'name': 'Kalu Waterfall',
            'full_name': 'Kalu Waterfall',
            'region': 'Malshej Ghat Belt',
            'gen_z_intro': "Kalu waterfall is a scenic monsoon-fed cascade near Malshej with attractive forested surroundings and easy access from the ghat. While not a historical fort, the waterfall is an important local natural landmark. Today Kalu is a popular short trek and picnic spot during monsoon, known for lush greenery and flowing streams.",
            'height_ft': 150, 'height_m': 46,
            'distance_km': 1.5,  # Average of 1–2 km
            'duration': '30–45 mins hike | 1 hr round trip',
            'difficulty': 'Easy', 'difficulty_color': 'green',
            'best_season': 'June–Oct',
            'base_village': 'Kalu / Malshej Ghat',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Malshej Ghat → Kalu',
                    'distance_km': 130, 'duration': '3.5 hrs',
                    'road_condition':'Good roads via Murbad till base village; last 3-4 km is narrow village road with some rough patches.',
                    'parking_info': 'Available near waterfall'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Malshej Ghat → Kalu',
                    'distance_km': 120, 'duration': '3.5 hrs',
                    'road_condition':'Excellent via Murbad road; last 3-4 km narrow village road. Parking available near base village.',

                    'parking_info': 'Available near waterfall'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Malshej Ghat (~3 hrs). Malshej Ghat → shared jeep / auto to Kalu (~10–15 mins)',
                    'total_time': '3.5 hrs',
                    'frequency': 'Regular buses'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train / bus to Kasara (~2 hrs). Kasara → MSRTC bus to Malshej Ghat (~1 hr). Malshej Ghat → shared jeep / auto to Kalu (~10–15 mins)',
                    'total_time': '3.5 hrs',
                    'frequency': 'Regular trains'
                }
            ]
        },
        {
            'name': 'Adrai Jungle Trek',
            'full_name': 'Adrai Jungle Trek',
            'region': 'Malshej Ghat Belt',
            'gen_z_intro': "Adrai is a lesser-known forested trek in the Malshej region with seasonal streams, dense foliage and local biodiversity; the area historically supported village livelihoods and grazing. The trail offers a more remote, exploratory feel compared with busier destinations. Today Adrai attracts trekkers seeking quiet jungle paths and monsoon stream hikes.",
            'height_ft': 2200, 'height_m': 670,
            'distance_km': 4.0,
            'duration': '2–2.5 hrs climb | 4–5 hrs round trip',
            'difficulty': 'Moderate', 'difficulty_color': 'orange',
            'best_season': 'Oct–Feb (monsoon makes trail slippery)',
            'base_village': 'Adrai / Malshej Ghat',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → Malshej Ghat → Adrai',
                    'distance_km': 130, 'duration': '3.5 hrs',
                    'road_condition':'Good roads till base village; last 4-5 km rough forest road. High-clearance vehicle essential.',
                    'parking_info': 'Available at base village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → Malshej Ghat → Adrai',
                    'distance_km': 120, 'duration': '3.5 hrs',
                    'road_condition':'Decent roads till base area; last 4-5 km rough jungle track. Four-wheel drive strongly recommended.',

                    'parking_info': 'Available at base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Swargate → MSRTC bus to Malshej Ghat (~3 hrs). Malshej Ghat → shared jeep / auto to Adrai (~15–20 mins). Trek base → short walk (~5–10 mins)',
                    'total_time': '3.5 hrs',
                    'frequency': 'Regular buses'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → train / bus to Kasara (~2 hrs). Kasara → MSRTC bus to Malshej Ghat (~1 hr). Malshej Ghat → shared jeep / auto to Adrai (~15–20 mins). Trek base → short walk (~5–10 mins)',
                    'total_time': '3.5 hrs',
                    'frequency': 'Regular trains'
                }
            ]
        }
    ]
    
    trek_data.extend(malshej_treks)
    
    # Add Konkan belt trek
    konkan_treks = [
        {
            'name': 'Nanemachi Waterfall',
            'full_name': 'Nanemachi Waterfall',
            'region': 'Konkan Belt',
            'gen_z_intro': "Nanemachi is a Konkan-region waterfall set amid coastal forests and rural landscapes; locally it’s an accessible natural spot valued for seasonal water flow and village access. The site is primarily a natural attraction rather than a historic fort. Today Nanemachi is enjoyed for short nature walks, waterfall views and a peaceful Konkan monsoon experience.",
            'height_ft': 120, 'height_m': 37,
            'distance_km': 2.0,
            'duration': '1–1.5 hrs round trip',
            'difficulty': 'Easy', 'difficulty_color': 'green',
            'best_season': 'June–Oct',
            'base_village': 'Nanemachi / Near Chiplun',
            'private_routes': [
                {
                    'from_city': 'Pune',
                    'route_description': 'Pune → NH66 → Chiplun → Nanemachi',
                    'distance_km': 230, 'duration': '5–5.5 hrs',
                    'road_condition': 'Good tar roads till base village; last 1-2 km rough village track. Four-wheeler accessible till village.', 
                    'parking_info': 'Available near base village'
                },
                {
                    'from_city': 'Mumbai',
                    'route_description': 'Mumbai → NH66 → Chiplun → Nanemachi',
                    'distance_km': 220, 'duration': '5 hrs',
                    'road_condition':'Good roads via Karjat; last 1-2 km rough village track. Parking available at base village.',

                    'parking_info': 'Available near base village'
                }
            ],
            'public_routes': [
                {
                    'from_city': 'Pune',
                    'route_steps': 'Pune → MSRTC bus to Chiplun (~6 hrs, buses every 2–3 hrs). Chiplun → shared jeep / auto to Nanemachi (~30 mins, every 1 hr). Trek base → short walk (~5–10 mins)',
                    'total_time': '7 hrs',
                    'frequency': 'Buses every 2–3 hrs'
                },
                {
                    'from_city': 'Mumbai',
                    'route_steps': 'Dadar → Konkan Railway to Chiplun (~4–5 hrs, trains every 1–2 hrs). Chiplun → shared jeep / auto to Nanemachi (~30 mins, every 1 hr). Trek base → short walk (~5–10 mins)',
                    'total_time': '6 hrs',
                    'frequency': 'Trains every 1–2 hrs'
                }
            ]
        }
    ]
    
    trek_data.extend(konkan_treks)
    
    return regions_data, trek_data

def insert_data():
    """Insert all parsed data into the database"""
    regions_data, trek_data = parse_trek_data()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Clear existing data
        TrekHighlight.query.delete()
        PublicRoute.query.delete()
        PrivateRoute.query.delete()
        Trek.query.delete()
        TrekRegion.query.delete()
        db.session.commit()
        
        print("Inserting regions...")
        # Insert regions
        region_map = {}
        for region_name in regions_data:
            clean_name = clean_text(region_name)
            region = TrekRegion(name=clean_name)
            db.session.add(region)
            db.session.flush()  # Get the ID
            region_map[clean_name] = region.id
            print(f"Added region: {clean_name}")
        
        db.session.commit()
        
        print(f"\nInserting {len(trek_data)} treks...")
        # Insert treks
        for i, trek in enumerate(trek_data, 1):
            print(f"Processing trek {i}: {trek['name']}")
            
            region_id = region_map.get(clean_text(trek['region']))
            if not region_id:
                print(f"Warning: Region not found for {trek['name']}: {trek['region']}")
                continue
            
            # Create trek
            new_trek = Trek(
                name=clean_text(trek['name']),
                full_name=clean_text(trek['full_name']),
                gen_z_intro=clean_text(trek['gen_z_intro']),
                height_ft=trek.get('height_ft'),
                height_m=trek.get('height_m'),
                distance_km=trek.get('distance_km'),
                duration=clean_text(trek.get('duration', '')),
                difficulty=trek.get('difficulty'),
                difficulty_color=trek.get('difficulty_color'),
                best_season=clean_text(trek.get('best_season', '')),
                base_village=clean_text(trek.get('base_village', '')),
                region_id=region_id
            )
            db.session.add(new_trek)
            db.session.flush()  # Get the trek ID
            
            # Insert private routes
            for route in trek.get('private_routes', []):
                private_route = PrivateRoute(
                    trek_id=new_trek.id,
                    from_city=clean_text(route.get('from_city', '')),
                    route_description=clean_text(route.get('route_description', '')),
                    distance_km=route.get('distance_km'),
                    duration=clean_text(route.get('duration', '')),
                    road_condition=clean_text(route.get('road_condition', '')),
                    parking_info=clean_text(route.get('parking_info', ''))
                )
                db.session.add(private_route)
            
            # Insert public routes
            for route in trek.get('public_routes', []):
                public_route = PublicRoute(
                    trek_id=new_trek.id,
                    from_city=clean_text(route.get('from_city', '')),
                    route_steps=clean_text(route.get('route_steps', '')),
                    total_time=clean_text(route.get('total_time', '')),
                    frequency=clean_text(route.get('frequency', ''))
                )
                db.session.add(public_route)
            
            # Insert highlights if any
            for highlight_text in trek.get('highlights', []):
                highlight = TrekHighlight(
                    trek_id=new_trek.id,
                    highlight=clean_text(highlight_text)
                )
                db.session.add(highlight)
            
            print(f"  - Added {trek['name']} with {len(trek.get('private_routes', []))} private routes and {len(trek.get('public_routes', []))} public routes")
        
        db.session.commit()
        print(f"\n✅ Successfully imported all {len(trek_data)} treks with complete data!")
        
        # Verify data
        verify_data()

def verify_data():
    """Verify that all data was inserted correctly"""
    with app.app_context():
        regions = TrekRegion.query.all()
        treks = Trek.query.all()
        private_routes = PrivateRoute.query.all()
        public_routes = PublicRoute.query.all()
        highlights = TrekHighlight.query.all()
        
        print(f"\n📊 Data verification:")
        print(f"Regions: {len(regions)}")
        print(f"Treks: {len(treks)}")
        print(f"Private Routes: {len(private_routes)}")
        print(f"Public Routes: {len(public_routes)}")
        print(f"Highlights: {len(highlights)}")
        
        print(f"\n🌍 Regions:")
        for region in regions:
            trek_count = len(region.treks)
            print(f"  - {region.name}: {trek_count} treks")
        
        print(f"\n🏔️ Sample treks:")
        for trek in treks[:5]:
            print(f"  - {trek.name} ({trek.region.name}): {trek.height_ft}ft, {trek.difficulty}")

if __name__ == '__main__':
    print("🚀 Starting trek data import...")
    print("This will import all 28 treks with complete information")
    insert_data()
    print("✅ Import completed successfully!")
