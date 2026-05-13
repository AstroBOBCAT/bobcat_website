from django.shortcuts import render
from sourcepage.models import Papers


def papers_list(request):
    # Fetch all papers from the database
    all_papers = Papers.objects.all()

    # Pass them to the template as 'papers'
    context = {
        'papers': all_papers
    }
    return render(request, 'mainpage/papers_list.html', context)