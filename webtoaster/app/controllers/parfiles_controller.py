from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import *
from django.template import Context, RequestContext
from django.template import loader
from app.models import *
from httplib import HTTPResponse
from lib.toaster import Pulsars
from lib.toaster import Parfiles

from django.core.context_processors import csrf
from django.conf import settings

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
import oauth2

from django.contrib.auth.decorators import login_required
from django import forms

from django.core.paginator import Paginator



class ParfileForm(forms.Form):
  name = forms.CharField()

def index(request):
  parfiles = Parfiles.show()

  t = loader.get_template('parfiles/index.html')
  c = RequestContext(request, {
    'parfiles': parfiles,
    })
  return HttpResponse(t.render(c))

def new(request):
  import os
  if request.method == 'POST' and request.FILES.get('parfile'):
    try:
      uf = request.FILES['parfile']
      temp_path = settings.TEMP_DIR
      fn = uf.name
      file_path = os.path.join( temp_path, fn )
      open( file_path, 'w' ).write( uf.read() )
      load_status = Parfiles.upload( username=request.user.username, path=file_path )
      request.session['flash'] = { 'type': 'success', 'message': 'Par file was loaded.'}
    except Exception as e:
      request.session['flash'] = { 'type': 'error', 'message': 'There was an error loading Par file. Message: %s' % str(e) }
      return redirect('/webtoaster/parfiles/new')
    return redirect('/webtoaster/parfiles')

  t = loader.get_template('parfiles/new.html')
  c = RequestContext(request, {
    })
  c.update(csrf(request))
  return HttpResponse(t.render(c))

def destroy(request, parfile_id):
  parfile_id = int( parfile_id )
  
  try:
    response = Parfiles.destroy( parfile_id )
    request.session['flash'] = { 'type': 'success', 'message': 'Par file was deleted.'}
  except Exception as e:
    request.session['flash'] = { 'type': 'error', 'message': 'Toaster produced an error while deleting Par file. Message: %s' % str(e) }

  if request.GET.get('after'):
    redirect_url = request.GET.get('after')
  else:
    redirect_url = '/webtoaster/parfiles'

  return redirect( redirect_url )

def download(request, parfile_id):
  from django.http import HttpResponse
  from django.core.servers.basehttp import FileWrapper
  import os 
  parfile = Parfiles.show(parfile_id=int(parfile_id) )[0]

  file_name = parfile.filename
  try:
    myfile = file(os.path.join(parfile.filepath, parfile.filename) )
  except:
    request.session['flash'] = { 'type': 'error', 'message': 'Could not open the requested file.' }
    return redirect( '/webtoaster/parfiles' )

  response = HttpResponse(myfile, content_type='application/par')
  response['Content-Disposition'] = "attachment; filename=%s" % file_name
  return response

def view(request, parfile_id):
  from django.http import HttpResponse
  from django.core.servers.basehttp import FileWrapper
  import os 
  parfile = Parfiles.show(parfile_id=int(parfile_id) )[0]

  filename = parfile.filename
  try:
    myfile = file(os.path.join(parfile.filepath, parfile.filename) )
  except:
    request.session['flash'] = { 'type': 'error', 'message': 'Could not open the requested file.' }
    return redirect( '/webtoaster/parfiles' )


  t = loader.get_template('parfiles/view.html')
  c = RequestContext(request, {
    'filename': filename,
    'filecontent': myfile.read()
    })
  c.update(csrf(request))
  return HttpResponse(t.render(c))
  return response