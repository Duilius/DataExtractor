from jinja2 import Environment, FileSystemLoader

def generate_email_content(template_name, data):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(f'{template_name}.html')
    return template.render(data=data)

# Uso:
# content = generate_email_content('email_template1', {'name': 'John', 'items': [...]})