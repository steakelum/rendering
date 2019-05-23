# REQUIRES MODIFIED VAPORY PACKAGE
# https://github.com/steakelum/vapory

from vapory import *
from threading import Thread

import numpy as np
import io, os, time, ffmpy, math, sys, time


rendering = "serial"				# leave at serial, parallel not properly implemented

class rendersettings:				# these settings affect the "image" of the render
	path = "render/"
	rendersize = 500				#1000x1000px
	antialiasing = 1
	quality = 11
	tweening = False				# to be implemented, placeholder for now

class fnsettings:
	pass

def lerp(v1, v2, f):
	if len(v1) != len(v2):
		print("lerp requires same size vector")
		return
	return [v1[i] + f*(v2[i] - v1[i]) for i in range(len(v2))]

def findranges(renderpoints): 		# finds the camera target and bounding box
	max_xyz = renderpoints[0][0].copy()
	min_xyz = renderpoints[0][0].copy()

	for anim in renderpoints:
		for seq in anim:
			for idx, val in enumerate(seq):
				max_xyz[idx] = max(max_xyz[idx], val)
				min_xyz[idx] = min(min_xyz[idx], val)


	#endpoints = [x[len(x)-1] for x in renderpoints]	#create list of all the last (settled) [x,y] points 
	#avg = [0 for x in renderpoints[0][0]]			#find their average for the camera target
	#for vector in endpoints:						#for each settled point, add its values to the global n-dimensional sum
	#	for i in range(len(vector)):
	#		avg[i] += vector[i]
	#avg = [t/len(endpoints) for t in avg]			#change sum to average
	#
	#furthest = max( [np.sqrt((renderpoints[i][0] - avg[i]).dot(renderpoints[i][0] - avg[i])) for i in range(len(renderpoints))] )
	return max_xyz, min_xyz



def render_setup(pointlist):

	try:
		os.mkdir(rendersettings.path)
	except FileExistsError:
		pass

	fnsettings.render_objects = []		# set up "template" for all objects in every scene
	
	mxbounds, mnbounds = findranges(pointlist)	# find the bounding box, i.e. domain of all points

												# set a ball/point size proportional to the map size
	fnsettings.pointsize = np.sqrt(np.sum(np.array(mxbounds)**2 + np.array(mnbounds)**2, axis=0))*.0075

	mxbounds = list(map(np.multiply,[1.1,1.1,1.1], mxbounds))
	mnbounds = list(map(np.multiply,[1.1,1.1,1.1], mnbounds))

	fnsettings.bounding = Box(mxbounds, mnbounds) 	

	fnsettings.cam_pos = list(map(np.multiply,[1,4,1],lerp(mnbounds, mxbounds, 1.25)))	#make the camera somewhere outside the map and (hopefully) viewing all of it

	fnsettings.cam_tgt = lerp(mnbounds, mxbounds, 0.5)	# make it look at the middle of the scene
	fnsettings.cam_tgt[1] = mnbounds[1]

	fnsettings.render_objects.append(Background('color',[.01,.01,.01]))		# needs a camera and a light source / background
	fnsettings.render_objects.append(LightSource( fnsettings.cam_pos, 'color', [1,1,1] ))

	fnsettings.render_objects.append(Isosurface(
			Function(fnsettings.function_str),
			'max_gradient',7,
			ContainedBy(fnsettings.bounding),
			'open',
			Texture(
				Pigment('color',fnsettings.function_clr),
				Finish('phong',0)			
			)))

def render_scene(keyframes, frame_count, fc_max):

	digits = len(str(fc_max))
	objects = fnsettings.render_objects.copy()

	for index, point in enumerate(keyframes):
		objects.append(Sphere(
			point[frame_count],
			fnsettings.pointsize,
			Texture(
				Pigment('color',[0.7,0,0]),
				Finish('phong', 0)
				)
			))


	scene = Scene( 
		Camera( 'location', fnsettings.cam_pos,
				'look_at', fnsettings.cam_tgt ), 
		objects= objects
		)


	filename = "frame_" + str(frame_count).zfill(int(digits)) 
	path = rendersettings.path + str(frame_count).zfill(int(digits)) + "/"

	tdif = time.time() - fnsettings.start_time
	exptime = (tdif / (frame_count - 1))*(1 + fc_max - frame_count) if frame_count > 1 else fc_max

	sys.stdout.write("\r\trendering frame {} of {}, ETA {} sec{}".format(frame_count, fc_max, round(exptime,2), " "*10))
	sys.stdout.flush()

	os.mkdir(path)
	#print(path + filename)
	try:
		scene.render(path + filename, width=rendersettings.rendersize, height=rendersettings.rendersize, quality=rendersettings.quality,antialiasing=rendersettings.antialiasing)
	except:
		print("render error, retrying:")
		scene.render(path + filename, width=rendersettings.rendersize, height=rendersettings.rendersize, quality=rendersettings.quality,antialiasing=rendersettings.antialiasing)
	os.rename(path + filename + ".png", rendersettings.path + filename + ".png")
	os.rmdir(path)


def ffmconvert(fps, path, vf, fc):
	digits = len(str(fc))
	ffmpy.FFmpeg(
		inputs={path + 'frame_%0{}d.png'.format(digits):['-r', str(fps),
				'-hide_banner', '-loglevel', 'panic']},
		outputs={'animation.{}'.format(vf):None}
		).run()
	return

# start actual rendering process
			# your algorithm must generate a list of frames for each involved point
			# for example: if you want to render 3 points and their trajectories, the function would return:
			# [ [[3,3,3], [2,2,2], [1,1,1], [0,0,0]],
			#	[[2,2,2,], [1,1,1], ......
			#	[[N,N,N],......	]	]
def render(keyframes, string, vformat, color = [0,1,1], fps=30):

	maxthreads = os.cpu_count()
	threads = []

	if os.path.exists("animation.{}".format(vformat)):
		if(input("animation file already exists in current directory. overwrite?")[0] == "y"):
			os.remove("animation.{}".format(vformat))
		else:
			return

	maxframes = len(max(keyframes, key = len))
	if(input("Are you sure you want to render " + str(maxframes) + " frames?")[0] == "y"):

		fnsettings.function_clr = color
		fnsettings.function_str = string

		render_setup(keyframes)

		print("starting rendering")

		fnsettings.start_time = time.time()
		currentframe = 0
		stopflag = False
		while True:
			stopflag = True
			for frameset in keyframes:
				if currentframe < len(frameset):
					stopflag = False				# some objects may settle before others i.e. there's less frames than others
			if(stopflag):
				break

			#render_scene(keyframes, currentframe, maxframes)

			threadobject = Thread(target = render_scene, args = (keyframes, currentframe, maxframes))
			threads.append(threadobject)

			currentframe += 1

		if rendering == "serial":
			for job in threads:
				job.start()
				job.join()
				# print("finished frame")

		elif rendering == "parallel":
			while len(threads) > 0:
				for thread in threads:
					thread.start()

				while True:
					alive = False
					for thread in threads:
						if thread.isAlive():
							alive = True
							break
					if not alive:
						break

				print("finished " + str(maxthreads) + " frames")
				threads = threads[maxthreads:]

		print("\nfinished rendering")

		ffmconvert(fps, rendersettings.path, vformat, maxframes)
		print("animation created, cleaning up")
		
		for file in os.listdir(rendersettings.path):
			os.remove(rendersettings.path + file)
		os.rmdir(rendersettings.path)

		if os.path.exists("__temp__.pov"):
			os.remove("__temp__.pov")

		print("done.")
