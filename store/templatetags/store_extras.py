from django import template

register = template.Library()

@register.filter(name='call')
def call_method(obj, method_name):
    """
    Chama um método do objeto fornecido com o nome do método fornecido.

    Uso:
    {{ object|call:method_name }}

    Exemplo:
    {{ review.is_marked_helpful_by|call:request.user }}
    """
    method = getattr(obj, method_name)
    if callable(method):
        return method
    return None

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Obtém um item de um dicionário pelo valor da chave.

    Uso:
    {{ dictionary|get_item:key }}

    Exemplo:
    {{ rating_distribution|get_item:5 }}
    """
    return dictionary.get(key)
