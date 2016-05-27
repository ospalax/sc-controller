#!/usr/bin/env python2

"""
Python wrapper for some X-related stuff.
"""

from ctypes import CDLL, POINTER, c_void_p, Structure, byref, cast
from ctypes import c_long, c_ulong, c_int, c_uint, c_short, c_char_p
from ctypes import c_ushort, c_ubyte, c_char_p, c_bool


def _load_lib(*names):
	"""
	Tries multiple alternative names to load .so library.
	"""
	for l in names:
		try:
			return CDLL(l)
		except OSError:
			pass
	raise OSError("Failed to load %s, library not found" % (names[0],))


libXFixes = _load_lib('libXfixes.so', 'libXfixes.so.3')
libX11 = _load_lib('libX11.so', 'libX11.so.6')


# Types
XID = c_ulong
Atom = c_ulong
XserverRegion = c_ulong
Display = c_void_p

# Structures
class XRectangle(Structure):
	_fields_ = [
		('x', c_short),
		('y', c_short),
		('width', c_ushort),
		('height', c_ushort),
	]


class XkbStateRec(Structure):
	_fields_ = [
		('group', c_ubyte),
		('locked_group', c_ubyte),
		('base_group', c_ushort),
		('latched_group', c_ushort),
		('mods', c_ubyte),
		('base_mods', c_ubyte),
		('latched_mods', c_ubyte),
		('locked_mods', c_ubyte),
		('compat_state', c_ubyte),
		('grab_mods', c_ubyte),
		('compat_grab_mods', c_ubyte),
		('lookup_mods', c_ubyte),
		('compat_lookup_mods', c_ubyte),
		('ptr_buttons', c_ushort),
	]


# Consants
SHAPE_BOUNDING	= 0
SHAPE_CLIP		= 1
SHAPE_INPUT		= 2

XKBUSECOREKBD	= 0x0100
ANYPROPERTYTYPE	= 0L
SUCCESS			= 0


# Functions
create_region = libXFixes.XFixesCreateRegion
create_region.argtypes = [ c_void_p, POINTER(XRectangle), c_int ]
create_region.restype = XserverRegion
set_window_shape_region = libXFixes.XFixesSetWindowShapeRegion
set_window_shape_region.argtypes = [ c_void_p, XID, c_int, c_int, c_int, XserverRegion ]
destroy_region = libXFixes.XFixesDestroyRegion
destroy_region.argtypes = [ c_void_p, XserverRegion ]
open_display = libX11.XOpenDisplay
open_display.argtypes = [ c_char_p ]
open_display.restype = c_void_p
xfree = libX11.XFree
xfree.argtypes = [ c_void_p ]
get_default_root_window = libX11.XDefaultRootWindow
get_default_root_window.argtypes = [ c_void_p ]
flush = libX11.XFlush
flush.argtypes = [ c_void_p ]
warp_pointer = libX11.XWarpPointer
warp_pointer.argtypes = [ c_void_p, XID, XID, c_int, c_int, c_int, c_int, c_int, c_int ]
query_pointer = libX11.XQueryPointer
query_pointer.argtypes = [ c_void_p, XID, POINTER(XID), POINTER(XID),
	POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_uint) ]
get_geometry = libX11.XGetGeometry
get_geometry.argtypes = [ c_void_p, XID, POINTER(XID), POINTER(c_int), POINTER(c_int),
	POINTER(c_uint), POINTER(c_uint), POINTER(c_uint), POINTER(c_uint) ]
get_input_focus = libX11.XGetInputFocus
get_input_focus.argtypes = [ c_void_p, POINTER(XID), POINTER(c_int) ]
get_window_property = libX11.XGetWindowProperty
get_window_property.argtypes = [ c_void_p, XID, Atom, c_long, c_long, c_bool,
	Atom, POINTER(Atom), POINTER(Atom), POINTER(c_ulong), POINTER(c_ulong),
	POINTER(c_void_p) ]
get_window_property.restype = c_int
intern_atom = libX11.XInternAtom
intern_atom.argtypes = [ c_void_p, c_char_p, c_bool ]
intern_atom.restype = Atom



# Wrapped functions
_xkb_get_state = libX11.XkbGetState
_xkb_get_state.argtypes = [c_void_p, c_uint, POINTER(XkbStateRec)]

# Wrappers
def get_xkb_state(dpy):
	rec = XkbStateRec()
	_xkb_get_state(dpy, XKBUSECOREKBD, rec)
	return rec


def get_window_size(dpy, window):
	root_return = XID()
	x, y = c_int(), c_int()
	width, height = c_uint(), c_uint()
	border_width, depth = c_uint(), c_uint()
	get_geometry(dpy, window, byref(root_return), byref(x), byref(y),
		byref(width), byref(height), byref(border_width), byref(depth))
	# print x, y, width, height
	return width.value, height.value


def get_screen_size(dpy):
	return get_window_size(dpy, get_default_root_window(dpy))


def get_mouse_pos(dpy, relative_to=None):
	"""
	Returns mouse position relative to specified window or to screen, if no
	window is specified.
	"""
	if relative_to is None:
		relative_to = get_default_root_window(dpy)
	root_return, child = XID(), XID()
	x, y = c_int(), c_int()
	child_x, child_y = c_int(), c_int()
	mask = c_uint()
	
	query_pointer(dpy, relative_to, byref(root_return), byref(child),
		byref(x), byref(y),
		byref(child_x), byref(child_y), byref(mask))
	return x.value, y.value


def set_mouse_pos(dpy, x, y, relative_to=None):
	"""
	Sets mouse position relative to specified window or to screen, if no
	window is specified.
	"""
	if relative_to is None:
		relative_to = get_default_root_window(dpy)
	warp_pointer(dpy, 0, relative_to, 0, 0, 0, 0, x, y)
	flush(dpy)


def get_current_window(dpy):
	"""
	Returns active window or root window if there is no active.
	"""
	# Try using WM-provided info first
	NET_ACTIVE_WINDOW = intern_atom(dpy, "_NET_ACTIVE_WINDOW", False)
	type_return, format_return = Atom(), Atom()
	nitems, bytes_after = c_ulong(), c_ulong()
	prop = c_void_p()
	
	if SUCCESS == get_window_property(dpy, get_default_root_window(dpy),
				NET_ACTIVE_WINDOW, 0, 2, False, ANYPROPERTYTYPE,
				byref(type_return), byref(format_return), byref(nitems),
				byref(bytes_after), byref(prop)):
		rv = cast(prop, POINTER(Atom)).contents.value
		xfree(prop)
		return rv
	
	# Fall-back to something what probably can't work anyway
	win, revert_to = XID(), c_int()
	get_input_focus(dpy, byref(win), byref(revert_to))
	if win == 0:
		return get_default_root_window(dpy)
	return win
