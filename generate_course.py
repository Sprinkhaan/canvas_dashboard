import json
from canvasapi import Canvas
from lib.lib_bandwidth import bandwidth_builder
from lib.lib_date import API_URL, get_date_time_obj
from lib.file import read_start, read_config
from model.Assignment import Assignment
from model.Student import Student
from model.perspective.StudentPerspective import StudentPerspective
from model.perspective.StudentPerspectives import StudentPerspectives


def get_dates(input):
    if input['due_at']:
        assignment_date = get_date_time_obj(input['due_at'])
    else:
        if input['lock_at']:
            assignment_date = get_date_time_obj(input['lock_at'])
        else:
            assignment_date = start.end_date
    if input['unlock_at']:
        unlock_date = get_date_time_obj(input['unlock_at'])
    else:
        unlock_date = start.start_date
    return unlock_date, assignment_date


def link_teachers():
    print('Link teachers to student_groups and assignment_groups')
    for teacher in config.teachers:
        for studentGroupId in teacher.projects:
            studentGroup = config.find_student_group(studentGroupId)
            if studentGroup:
                studentGroup.teachers.append(teacher.id)
        for assignmentGroupId in teacher.assignment_groups:
            assignmentGroup = config.find_assignment_group(assignmentGroupId)
            if assignmentGroup:
                assignmentGroup.teachers.append(teacher.id)

start = read_start()
config = read_config(start.config_file_name)
print("Config", config)


# Initialize a new Canvas object
canvas = Canvas(API_URL, start.api_key)
user = canvas.get_current_user()
print(user.name)

canvas_course = canvas.get_course(start.course_id)

link_teachers()

# course = Course(canvas_course.id, canvas_course.name, actual_date.strftime(DATE_TIME_STR))

# Ophalen Students
users = canvas_course.get_users(enrollment_type=['student'])
config.students = []
for user in users:
    print(user.name, user.login_id)
    student = Student(user.id, 0, user.name, 'None', "", user.login_id, "", 0)
    config.students.append(student)


# Ophalen Secties en Roles
print("Ophalen student secties uit Canvas deze koppelen aan Role ")
course_sections = canvas_course.get_sections(include=['students'])
for course_section in course_sections:
    # use only relevant sections
    section = config.find_section(course_section.id)
    if section:
        # print("course_section", section)
        course_section_students = course_section.students
        if course_section_students:
            for section_student in course_section_students:
                student_id = section_student["id"]
                student = config.find_student(student_id)
                if student:
                    student.role = section.role

print("Opschonen studenten zonder Role")
for student in config.students:
    if len(student.role) == 0:
        config.students.remove(student)
config.student_count = len(config.students)

# Perspectives toevoegen aan Students
print("Toevoegen Perspectives aan Student")
for student in config.students:
    student.perspectives = StudentPerspectives()
    for perspective_key in config.perspectives.perspectives:
        print(perspective_key)
        if len(config.perspectives.perspectives[perspective_key].assignment_groups) > 1:
            # meerdere assignment_group: kennis
            student.perspectives.perspectives[perspective_key] = StudentPerspective(perspective_key, 0, 0, 0)
            assignment_group_id = config.find_assignment_group_by_role(student.role)
            student.perspectives.perspectives[perspective_key].assignment_groups.append(assignment_group_id)
        elif len(config.perspectives.perspectives[perspective_key].assignment_groups) == 1:
            # één assignment_group: team, gilde en peil
            student.perspectives.perspectives[perspective_key] = StudentPerspective(perspective_key, 0, 0, 0)
            assignment_group_id = config.perspectives.perspectives[perspective_key].assignment_groups[0]
            student.perspectives.perspectives[perspective_key].assignment_groups.append(assignment_group_id)
        else:
            print("ERROR: geen assignment_group for perspective")

# Students en StudentGroups koppelen
canvas_group_categories = canvas_course.get_group_categories()
for canvas_group_category in canvas_group_categories:
    print(canvas_group_category)
    # ophalen projectgroepen
    if canvas_group_category.name == start.projects_groep_name:
        canvas_groups = canvas_group_category.get_groups()
        for canvas_group in canvas_groups:
            print(canvas_group)
            studentGroup = config.find_student_group(canvas_group.id)
            if studentGroup:
                canvas_users = canvas_group.get_users()
                for canvas_user in canvas_users:
                    student = config.find_student(canvas_user.id)
                    if student:
                        student.group_id = studentGroup.id
                        if len(studentGroup.teachers) > 0:
                            student.coach_initials = config.find_teacher(studentGroup.teachers[0]).initials
                        studentGroup.students.append(student)
    # ophalen slb-groepen
    if canvas_group_category.name == start.slb_groep_name:
        canvas_groups = canvas_group_category.get_groups()
        for canvas_group in canvas_groups:
            print(canvas_group)
            slb_group = config.find_slb_group(canvas_group.id)
            if slb_group:
                canvas_users = canvas_group.get_users()
                for canvas_user in canvas_users:
                    student = config.find_student(canvas_user.id)
                    if student:
                        slb_group.students.append(student)

# Ophalen Assignments bij de AssignmentsGroups
canvas_assignment_groups = canvas_course.get_assignment_groups(include=['assignments', 'overrides', 'online_quiz'])
for canvas_assignment_group in canvas_assignment_groups:
    # use only relevant assignment_groups
    assignment_group = config.find_assignment_group(canvas_assignment_group.id)
    if assignment_group:
        print("assignment_group", canvas_assignment_group)
        group_points_possible = 0
        for canvas_assignment in canvas_assignment_group.assignments:
            if canvas_assignment['points_possible']:
                group_points_possible += canvas_assignment['points_possible']
                points_possible = canvas_assignment['points_possible']
            else:
                points_possible = 0

            # l_submission_types = canvas_assignment['submission_types']
            # print(l_submission_types)
            # if 'external_tool' in l_submission_types:
            #     print(canvas_assignment['quiz_id'])
            if canvas_assignment['overrides']:
                for overrides in canvas_assignment['overrides']:
                    unlock_date, assignment_date = get_dates(overrides)
                    if 'course_section_id' in overrides.keys():
                        section_id = overrides['course_section_id']
                    else:
                        section_id = 0
                    assignment = Assignment(canvas_assignment['id'], canvas_assignment['name'], canvas_assignment['assignment_group_id'], section_id, points_possible, assignment_date, unlock_date)
                    print("OVERRIDE", assignment)
                    assignment_group.append_assignment(assignment)
            else:
                unlock_date, assignment_date = get_dates(canvas_assignment)
                section_id = 0
                assignment = Assignment(canvas_assignment['id'], canvas_assignment['name'],
                                    canvas_assignment['assignment_group_id'], section_id,
                                    points_possible, assignment_date, unlock_date)
                print(assignment)
                assignment_group.append_assignment(assignment)
        print(assignment_group.name, assignment_group.total_points, group_points_possible)
        # assignment_group.total_points = group_points_possible

for assignment_group in config.assignment_groups:
    assignment_group.bandwidth = bandwidth_builder(assignment_group, config.days_in_semester)

with open(start.course_file_name, 'w') as f:
    dict_result = config.to_json(["assignment"])
    json.dump(dict_result, f, indent=2)
