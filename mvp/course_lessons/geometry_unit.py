# Geometry:
# Lesson 1: Points Lines and Planes and stuff
# Have them learn about the basis of geometry and the exercises will we T or F
# Lesson 2: Angles
# Have them learn about acute straight obtuse and stuff and the exercises will be for them to identify what is each one
# Lesson 3: Triangles Pt. 1
# Teach them types of triangles, and the exercises will be identifying them
# Lesson 4: Triangles Pt. 2
# We will teach them the formulas such as Pythagorean Theorem or triangular inequality and the exercises will be for them to solve questions using those formulas
# Lesson 5: Quadrilaterals and Polygons
# We can teach them stuff like squares and the exercises will be to name the polygons
# Lesson 6: Circles Pt. 1
# We teach them about circles and what is a circle and what isn’t and the problems would be to identify what is and what isn't
# Lesson 7: Circle Pt. 2
# We teach them about the formulas such as the ones for radius, diameter, circumference, chords, arcs, and central/inscribed angles and the problems would be to let them solve using the formulas
# Lesson 8: Perimeter, Area, and Volume
# Teach them all the formulas (this lesson could be broken into smaller pieces)
# Lesson 9: Unit Review


# geometry_unit.py
UNIT_GEOMETRY = {
  "unit_id": "u_geo",
  "title": "Geometry Fundamentals",
  "unit_reward": {"coins": 100, "chest": "Gold Chest"},
  "lessons": [
    # Lesson 1: Points, Lines, Planes
    {"lesson_id": "g1", "type": "article", "title": "Points, Lines, and Planes",
     "body": "A point has no size. A line has length but no thickness and extends forever in two directions. A plane is a flat surface that extends forever."},
    {"lesson_id": "g2", "type": "quiz", "title": "True or False: Basics",
     "questions": [
       {"qid": "g2_q1", "prompt": "A point has length and width", "options": ["True", "False", "Sometimes", "Only in 3D"], "answer_index": 1, "explanation": "A point has no dimensions."},
       {"qid": "g2_q2", "prompt": "Two distinct points determine exactly one line", "options": ["True", "False", "Need three points", "Only if collinear"], "answer_index": 0, "explanation": "Postulate: two points determine a line."}
     ],
     "rewards": {"coins": 10}},

    # Lesson 2: Angles
    {"lesson_id": "g3", "type": "article", "title": "Angles",
     "body": "Acute is 0 to 90. Right is 90. Obtuse is 90 to 180. Straight is 180."},
    {"lesson_id": "g4", "type": "quiz", "title": "Identify Angles",
     "questions": [
       {"qid": "g4_q1", "prompt": "An angle measuring 37 degrees is", "options": ["Acute", "Right", "Obtuse", "Straight"], "answer_index": 0, "explanation": "Between 0 and 90 is acute."},
       {"qid": "g4_q2", "prompt": "An angle measuring 180 degrees is", "options": ["Acute", "Right", "Obtuse", "Straight"], "answer_index": 3, "explanation": "A straight angle is 180."}
     ],
     "rewards": {"coins": 10}},

    # Lesson 3: Triangles Pt. 1
    {"lesson_id": "g5", "type": "article", "title": "Types of Triangles",
     "body": "By sides: scalene, isosceles, equilateral. By angles: acute, right, obtuse."},
    {"lesson_id": "g6", "type": "quiz", "title": "Identify Triangle Type",
     "questions": [
       {"qid": "g6_q1", "prompt": "A triangle with sides 5, 5, 8 is", "options": ["Scalene", "Isosceles", "Equilateral", "Right"], "answer_index": 1, "explanation": "Two equal sides means isosceles."},
       {"qid": "g6_q2", "prompt": "A triangle with angles 30, 60, 90 is", "options": ["Acute", "Right", "Obtuse", "Equilateral"], "answer_index": 1, "explanation": "Contains a 90 degree angle so it is right."}
     ],
     "rewards": {"coins": 10}},

    # Lesson 4: Triangles Pt. 2
    {"lesson_id": "g7", "type": "article", "title": "Pythagorean and Triangle Inequality",
     "body": "Right triangles: a^2 + b^2 = c^2. Triangle inequality: sum of any two sides is greater than the third."},
    {"lesson_id": "g8", "type": "quiz", "title": "Triangle Formulas",
     "questions": [
       {"qid": "g8_q1", "prompt": "If legs are 6 and 8, the hypotenuse is", "options": ["10", "12", "7", "14"], "answer_index": 0, "explanation": "sqrt(6^2 + 8^2) = sqrt(100) = 10."},
       {"qid": "g8_q2", "prompt": "Can 2, 3, 6 form a triangle", "options": ["Yes", "No", "Only right triangle", "Only obtuse"], "answer_index": 1, "explanation": "2 + 3 is not greater than 6."}
     ],
     "rewards": {"coins": 10}},

    # Lesson 5: Quads and Polygons
    {"lesson_id": "g9", "type": "article", "title": "Quadrilaterals and Polygons",
     "body": "Square, rectangle, rhombus, parallelogram, trapezoid. Regular polygons have equal sides and angles."},
    {"lesson_id": "g10", "type": "quiz", "title": "Name the Polygon",
     "questions": [
       {"qid": "g10_q1", "prompt": "A polygon with 8 sides is a", "options": ["Heptagon", "Octagon", "Nonagon", "Decagon"], "answer_index": 1, "explanation": "Eight sides is octagon."},
       {"qid": "g10_q2", "prompt": "A parallelogram with four right angles is a", "options": ["Rhombus", "Square", "Rectangle", "Kite"], "answer_index": 2, "explanation": "Rectangle is a parallelogram with right angles."}
     ],
     "rewards": {"coins": 10}},

    # Lesson 6: Circles Pt. 1
    {"lesson_id": "g11", "type": "article", "title": "What is a Circle",
     "body": "All points in a plane at a fixed distance from a center."},
    {"lesson_id": "g12", "type": "quiz", "title": "Circle or Not",
     "questions": [
       {"qid": "g12_q1", "prompt": "All points 5 units from a fixed point in the plane", "options": ["Circle", "Line", "Parabola", "Ellipse"], "answer_index": 0, "explanation": "Definition of a circle."},
       {"qid": "g12_q2", "prompt": "All points 5 units from a fixed line", "options": ["Circle", "Parabola", "Two parallel lines", "Ellipse"], "answer_index": 2, "explanation": "This is a pair of parallel lines."}
     ],
     "rewards": {"coins": 10}},

    # Lesson 7: Circles Pt. 2
    {"lesson_id": "g13", "type": "article", "title": "Circle Formulas",
     "body": "Diameter 2r. Circumference 2πr. Area πr^2. Central angle subtends equal arc measure. Inscribed angle is half its intercepted arc."},
    {"lesson_id": "g14", "type": "quiz", "title": "Solve with Circle Formulas",
     "questions": [
       {"qid": "g14_q1", "prompt": "Circle with radius 7. Circumference is", "options": ["7π", "14π", "49π", "28π"], "answer_index": 1, "explanation": "2πr = 14π."},
       {"qid": "g14_q2", "prompt": "Inscribed angle intercepts a 100 degree arc. Angle measure is", "options": ["100", "50", "200", "25"], "answer_index": 1, "explanation": "Inscribed angle is half the arc."}
     ],
     "rewards": {"coins": 10}},

    # Lesson 8: Perimeter, Area, Volume
    {"lesson_id": "g15", "type": "article", "title": "Perimeter, Area, Volume",
     "body": "Perimeter is boundary length. Area is surface measure in square units. Volume is space in cubic units. Common formulas: rectangle A = lw, triangle A = 1/2 bh, cylinder V = πr^2h."},
    {"lesson_id": "g16", "type": "quiz", "title": "Compute P, A, or V",
     "questions": [
       {"qid": "g16_q1", "prompt": "Rectangle with l = 10 and w = 4. Area is", "options": ["14", "40", "28", "20"], "answer_index": 1, "explanation": "A = lw = 40."},
       {"qid": "g16_q2", "prompt": "Cylinder with r = 3 and h = 5. Volume is", "options": ["15π", "30π", "45π", "90π"], "answer_index": 2, "explanation": "πr^2h = 9π*5 = 45π."}
     ],
     "rewards": {"coins": 10}},

    # Lesson 9: Review
    {"lesson_id": "g17", "type": "quiz", "title": "Unit Review Mini Test",
     "questions": [
       {"qid": "g17_q1", "prompt": "Two angles that form a line are", "options": ["Complementary", "Vertical", "Straight", "Linear pair"], "answer_index": 3, "explanation": "A linear pair forms a straight line."},
       {"qid": "g17_q2", "prompt": "Right triangle with legs 9 and 12. Hypotenuse is", "options": ["15", "21", "10", "13"], "answer_index": 0, "explanation": "9^2 + 12^2 = 225 gives 15."}
     ],
     "rewards": {"coins": 30}}
  ]
}
