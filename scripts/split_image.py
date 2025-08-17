import os
import random
from PIL import Image

# ------------------------------
# Example female first & last names
# ------------------------------
female_first_names = [
    "Alice", "Sophia", "Emma", "Olivia", "Mia", "Amelia",
    "Ella", "Grace", "Hannah", "Chloe", "Charlotte", "Ava",
    "Isabella", "Lucy", "Lily", "Sophie", "Zoe", "Emily",
    "Abigail", "Madison", "Elizabeth", "Victoria", "Evelyn",
    "Harper", "Scarlett", "Penelope", "Lillian", "Layla",
    "Claire", "Bella", "Aurora", "Addison", "Natalie",
    "Gabriella", "Anna", "Ellie", "Aubrey", "Brooklyn",
    "Alexis", "Sadie", "Ariana", "Allison", "Hailey",
    "Peyton", "Alyssa", "Eleanor", "Aria", "Sarah",
    "Naomi", "Melanie", "Catherine", "Morgan", "Bailey",
    "Rebecca", "Katherine", "Stella", "Valentina", "Kennedy",
    "Everly", "Violet", "Luna", "Hazel", "Paisley",
    "Elena", "Elliana", "Ivy", "Eden", "Josephine"
]
 
# ------------------------------
# Example male first names (same count as female list)
male_first_names = [
    "Liam", "Noah", "Oliver", "Elijah", "William", "James",
    "Benjamin", "Lucas", "Henry", "Alexander", "Mason", "Michael",
    "Ethan", "Daniel", "Jacob", "Logan", "Jackson", "Levi",
    "Sebastian", "Mateo", "Jack", "Owen", "Theodore", "Aiden",
    "Samuel", "Joseph", "John", "David", "Wyatt", "Matthew",
    "Luke", "Asher", "Carter", "Julian", "Grayson", "Leo",
    "Jayden", "Gabriel", "Isaac", "Lincoln", "Anthony", "Hudson",
    "Dylan", "Ezra", "Thomas", "Charles", "Christopher", "Jaxon",
    "Maverick", "Josiah", "Isaiah", "Andrew", "Elias", "Joshua",
    "Nathan", "Caleb", "Ryan", "Adrian", "Miles", "Eli",
    "Nolan", "Christian", "Aaron", "Cameron", "Ezekiel", "Colton",
    "Luca", "Landon"
]

last_names = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller",
    "Davis", "Garcia", "Martinez", "Rodriguez", "Wilson",
    "Anderson", "Taylor", "Thomas", "Moore", "Martin", "Lee",
    # Additional common last names to match count
    "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen",
    "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall",
    "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Gomez",
    "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz",
    "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales",
    "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan",
    "Cooper", "Peterson", "Bailey"
]

 # ------------------------------
 # Load image and setup
 # ------------------------------
folder_path = "media/profile_photos"
# include folder path for input image
input_image = os.path.join(folder_path, "profile_grid_4.png")

img = Image.open(input_image)
width, height = img.size

# Divide into 3x3 = 9 squares
rows, cols = 3, 3
crop_width = width // cols
crop_height = height // rows

 # ------------------------------
 # Crop and save each square (ensure unique filenames)
 # ------------------------------
# track already used filenames
used_filenames = set()
for row in range(rows):
    for col in range(cols):
        left = col * crop_width
        upper = row * crop_height
        right = left + crop_width
        lower = upper + crop_height
        
        cropped_img = img.crop((left, upper, right, lower))
        
        # Generate unique name combination
        while True:
            first_name = random.choice(male_first_names)
            last_name = random.choice(last_names)
            filename = f"{first_name.lower()}_{last_name.lower()}.png"
            file_path = os.path.join(folder_path, filename)
            # ensure not already used or existing
            if filename not in used_filenames and not os.path.exists(file_path):
                used_filenames.add(filename)
                break
        cropped_img.save(file_path)

print("✅ Cropping complete! Images saved in:", folder_path)
