from django.http import Http404
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel
from django.shortcuts import get_object_or_404, render
from openai import OpenAI

from .models import Profile

client = OpenAI()


def index(request):
    context = {
    }
    return render(request, "jobs_board/index.html", context)


def profile(request, profile_id):
    profile_obj = get_object_or_404(Profile, pk=profile_id)
    context = {
        'profile': profile_obj,
        'profile_id': profile_id,
    }
    return render(request, "jobs_board/profile.html", context)


def profile_create(request):
    try: 
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        bio = request.POST['bio']
        new_profile = Profile(first_name=first_name, last_name=last_name, email=email, bio=bio)
        new_profile.save()
        print('saved new profile', new_profile)
        context = {
            'new_profile': new_profile,
        }
        # return render(request, "jobs_board/profile_create.html", context)
        return profile_evaluate(request, new_profile.id)
    except:
        context = {
        }
        return render(request, "jobs_board/profile_create.html", context)

class Skills(BaseModel):
    skills: list[str]

def profile_evaluate(request, profile_id):
    # profile_obj = get_object_or_404(Profile, pk=profile_id)
    profile_obj = None
    try:
        profile_obj = Profile.objects.get(pk=profile_id)
    except Profile.DoesNotExist:
        raise Http404("Profile does not exist")
    print('evaluating profile name', profile_obj.first_name, profile_obj.last_name)
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f"Extract the 3-6 skills from the perspective of a recruiter from the bio of {profile_obj.first_name} {profile_obj.last_name}. this person's bio: {profile_obj.bio}",
            }
        ],
        response_format=Skills,
    )
    skills = completion.choices[0].message.parsed.skills
    context = {
        'profile': profile_obj,
        'skills': skills,
    }
    profile_obj.save()
    return render(request, "jobs_board/profile_evaluate.html", context)
