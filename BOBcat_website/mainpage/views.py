from django.shortcuts import render
from sourcepage.models import BinaryModel


def binary_model_list(request):
    # Retrieve all binary models from the database
    # select_related is used to optimize the query since candidate_name is a ForeignKey
    binary_models = BinaryModel.objects.select_related('candidate_name').all()

    context = {
        'binary_models': binary_models
    }
    return render(request, 'binary_model_list.html', context)