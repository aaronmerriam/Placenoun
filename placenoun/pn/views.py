import random

from django.shortcuts import render_to_response
from django.template import RequestContext

try:
  from fractions import gcd
except ImportError:
  from placenoun.numberutilities.main import gcd

from placenoun.pn.models import NounStatic, NounExternal, SearchGoogle, SearchBing

def index(request):
  template = 'index.html'
  data = {}

  context = RequestContext(request)
  return render_to_response(template, data, context)

def get_by_id(request, id):
  id = int(id)
  this_image = NounExternal.objects.get(pk = id)
  return this_image.http_image

def noun_static(request, noun, width, height):
  width = min(2048, int(width))
  height = min(2048, int(height))

  noun_query = NounStatic.objects.filter(noun = noun, width = width, height = height)[:1]
  if noun_query:
    this_image = noun_query.get()
    return this_image.http_image

  noun_query = NounExternal.objects.filter(noun = noun, width = width, height = height, status__lt = 20)
  if noun_query.exists():
    this_image = noun_query[0]
    if not this_image.image:
      this_image.populate()
    if this_image.status == 10:
      this_image = this_image.to_static()
      return this_image.http_image

  aspect_gcd = gcd(width, height)
  aspect_width = width/aspect_gcd
  aspect_height = height/aspect_gcd
  noun_query = NounExternal.objects.filter(noun= noun, width__gte = width, height__gte = height, aspect_width = aspect_width, aspect_height = aspect_height, status__lt = 20)
  if noun_query.exists():
    this_image = noun_query[0]
    if not this_image.image:
      this_image.populate()
    if this_image.status == 10:
      this_image = this_image.to_static(size=(width, height))
      return this_image.http_image


  # At this point we couldn't find a suitable match, so... we'll serve
  # up a best fit result but it won't be perminant

  random.choice([SearchBing, SearchGoogle]).do_next_search(noun)

  radius = 1
  slope = float(height)/width
  while True:
    noun_query = NounExternal.get_knn_window(noun, slope, radius)
    noun_query = noun_query[0:]
    if not noun_query:
      radius = radius*2
      if radius > 64:
        radius = 1
        random.choice([SearchBing, SearchGoogle]).do_next_search(noun)
      continue

    noun_query = sorted(noun_query, key = lambda noun_obj: noun_obj.compare(width, height) )
    noun_query.reverse()
    while noun_query:
      this_image = noun_query.pop()
      if not this_image.image:
        this_image.populate()
      if not this_image.image:
        continue
      ret = this_image.http_image_resized(size=(width, height))
      return this_image.http_image_resized(size=(width, height))

def noun(request, noun):
  noun_query = NounExternal.objects.filter(noun = noun, status__lte = 30)
  if noun_query.exists():
    if noun_query.count() > 100:
      this_image = noun_query.order_by('?')[0]
      if not this_image.image:
        this_image.populate()
      if this_image.image:
        return this_image.http_image

  random.choice([SearchBing, SearchGoogle]).do_next_search(noun)

  while True:
    noun_query = NounExternal.objects.filter(noun = noun, status__lte = 30)
    if noun_query.exists():
      this_image = noun_query.order_by('?')[0]
      if not this_image.image:
        this_image.populate()
      if not this_image.image:
        continue
      return this_image.http_image
    else:
      random.choice([SearchBing, SearchGoogle]).do_next_search(noun)
