class Role:
    def __init__(self, short, name, btn_color):
        self.name = name
        self.short = short
        self.btn_color = btn_color
        # self.sections = []
        self.assignment_groups = []

    def to_json(self, scope):
        return {
            'short': self.short,
            'name': self.name,
            'btn_color': self.btn_color,
            # 'sections': list(map(lambda s: s.to_json(), self.sections)),
            'assignment_groups': self.assignment_groups,
        }

    def __str__(self):
        line = f' Role({self.short}, {self.name}, {self.btn_color}, {self.assignment_groups})\n'
        return line

    @staticmethod
    def from_dict(data_dict):
        new_role = Role(data_dict['short'], data_dict['name'], data_dict['btn_color'])
        # new_role.sections = list(map(lambda s: s, data_dict['sections']))
        new_role.assignment_groups = data_dict['assignment_groups']
        return new_role
