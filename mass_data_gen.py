#!/usr/bin/env python
'''
Reads from  NIST_isotope_data_2017.txt; the source of this data file is:
	http://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=&all=all&ascii=ascii2&isotype=all
	(copied from NIST website July 1, 2017)

Usage:
	>>> import mass_data_gen as m
	>>> els = m.main()
	
	>>> els['H'].__dict__
	{'abundances': [0.999885, 0.000115], 'atomic_num': '1', 'symbol': 'H', 'std_atomic_weight': '[1.00784,1.00811]', 'mass_num': '1', 'atomic_weight': 1.00794572105, 'masses': [1.00783, 2.0141]}
	
	>>> els['H'].atomic_weight
	1.00794572105
	
	>>> els['Ce'].atomic_num
	58
	
	>>> els['Ru'].masses
	[95.90759, 97.90529, 98.90593, 99.90421, 100.90558, 101.90434, 103.90543]
	
	>>> els['Si'].abundances
	[0.92223, 0.04685, 0.03092]
	
'''

import numpy as np
import json
import re

isotope_data_fields 		= ['atomic_num','symbol','mass_num','mass','abundance','std_atomic_weight']
isotope_data_map			= [int, str, int, float, lambda x: float(x) if x else None, lambda x: x]
element_data_fields 		= ['atomic_num','symbol','std_atomic_weight']

elements = {}

class isotope(object):
	'''Each NIST data entry is an isotope, used collectively to build elements from element() object'''
	def __init__(self, isotope_data):
		for i,f in enumerate(isotope_data_fields):
			val = isotope_data[i].split('=')[1].strip().split('(')[0]
			setattr(self, f, isotope_data_map[i](val) )
		if self.symbol in 'TD':
			self.symbol = 'H'


class element(object):
	''' Each element is built from individual isotope object data '''
	def __init__(self, isotope_obj):
		for i in element_data_fields:
			setattr(self, i, getattr(isotope_obj, i))		
		self.masses 	= []
		self.abundances = []
		self.isotopes 	= []
		
		self.add_mass(isotope_obj)

	def add_mass(self, isotope_obj):
		self.isotopes.append(isotope_obj)
		if isotope_obj.abundance:
			self.abundances.append( round( float( isotope_obj.abundance ), 5 ) )
			self.masses.append( 	round( float( isotope_obj.mass 		), 5 ) )


def process( all_isotope_data ):
	''' data is list of individual isotope lists, read from nist_el_data_linear.txt '''
	for isotope_data in all_isotope_data:		
		isotope_obj = isotope( isotope_data )

		if isotope_obj.symbol not in elements:
			elements[isotope_obj.symbol] = element(isotope_obj)	
		else:
			elements[isotope_obj.symbol].add_mass(isotope_obj)
	
	''' After the creation of all elements, get atomic weight from masses/abundances data '''
	for elem in elements:
		el = elements[elem]
		if el.abundances:
			el.atomic_weight = sum( np.array(el.masses) * np.array(el.abundances) ) 
		else:
			''' Attempt to extract atomic_weight from std_atomic_weight field
				Subtract weight (if available) from each isotope mass and sort the absolute difference
				Add the lowest value (after sorting) if the mass_diff_map has values < 1 '''
			mass_num_weight = re.sub('\[|\]','', el.std_atomic_weight) 
			iso_masses = [iso.mass for iso in el.isotopes]
			mass_diff_map = map( lambda x: abs( float(mass_num_weight) - x ) if mass_num_weight else x, iso_masses)# [ iso.mass for iso in el.isotopes ] )
			sorted_mass_map = [x for y,x in sorted(zip( mass_diff_map, iso_masses ))]
			
			el.atomic_weight = sorted_mass_map[0] if any([x < 1. for x in mass_diff_map]) else 'Unknown'


def write_json( elements ):
	''' json-encode element data for export '''

	el_json = { e : { x : getattr(elements[e],x) for x in elements[e].__dict__  if x != 'isotopes'} for e in elements}
	
	with open('elements.json','w') as f:
		f.write( json.dumps( el_json ) )
	

def main():

	with open('NIST_isotope_data_2017.txt') as f:
		process( [x.split('\n') for x in f.read().split('\n\n')] )
	
	write_json( elements )
		
	return elements
	
if __name__ == '__main__':
	main()