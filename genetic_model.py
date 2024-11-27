import matplotlib.pyplot as plt
import numpy as np
import pygame
import math

from macros import *
from bezier import *

PATH_DANGER_PRIORITIZE_FACTOR = 0.8
PATH_LENGTH_PRIORITIZE_FACTOR = 0.2

CROSSOVER_RATIO = 0.5
ELITISM_RATIO = 0.3
MUTATION_RATIO = 0.1
POPULATION = 200
CHROMOSOME_INITIAL_LENGTH = 5
NUM_GENERATIONS = 10000

def chromosome_to_bezier(chromosome):
    bezier = Bezier()
    bezier.control_points= np.array([
            gene
            for gene in chromosome
            ])
    return bezier

def fitness_function(chromosome,map,population):
    max_path_length = 0
    for chromo in population:
        bezier = chromosome_to_bezier(chromo)
        path_length = bezier.get_length()
        max_path_length = max(max_path_length, path_length)

    bezier = chromosome_to_bezier(chromosome)
    path_length = bezier.get_length()
    path_danger = measure_bezier_danger(chromosome, map)
    normalized_path_length = min(path_length / max_path_length, 1.0)
    if path_danger >= 0.2:
        return 100
    fitness = (
        PATH_LENGTH_PRIORITIZE_FACTOR * normalized_path_length +
        PATH_DANGER_PRIORITIZE_FACTOR * path_danger
    )
    return fitness

class Genetic_model:
    def __init__(self):
        print("Initializing Model")
        self.chromosomes = []
        self.fitness_scores = []
        self.elite_indices = []

    def generate_initial_population(self):
        print("Generating Intial Chromosomes")
        for _ in range(POPULATION):
            chromo = [START_POSITION]
            for __ in range(CHROMOSOME_INITIAL_LENGTH - 2):
                while(True):
                    gene = [np.random.randint(SCREEN_WIDTH), np.random.randint(SCREEN_HEIGHT)]
                    if gene != START_POSITION and gene != END_POSITION: break
                chromo.append(gene)
            chromo.append(END_POSITION)
            self.chromosomes.append(chromo)


    def evaluate_population(self, map):
        print("Evaluating Population")
        self.fitness_scores = [fitness_function(chromosome, map, self.chromosomes) for chromosome in self.chromosomes]

    def select_elites(self):
        num_elites = int(len(self.chromosomes) * ELITISM_RATIO)
        sorted_indices = np.argsort(self.fitness_scores)  
        self.elite_indices = sorted_indices[:num_elites] 

    def crossover(self):
        print("Performing Crossover")
        non_elite_indices = [i for i in range(len(self.chromosomes)) if i not in self.elite_indices] 
        num_crossover = int(len(non_elite_indices) * CROSSOVER_RATIO)
        chosen_parent_indices = np.random.choice(
                len(non_elite_indices), num_crossover, replace=False
                )
        for i in range(0,len(chosen_parent_indices)-1, 2):
            mom = self.chromosomes[chosen_parent_indices[i]]
            dad = self.chromosomes[chosen_parent_indices[i+1]]
            min_length = min(len(mom), len(dad)) # perform randomize with the smaller gene length
            cross_over_point = np.random.randint(1, min_length - 1) # ignore start and end genes
            son = mom[:cross_over_point] + dad[cross_over_point:]
            daughter = dad[:cross_over_point] + mom[cross_over_point:]
            # overwrite mom and dad with 2 children
            self.chromosomes[chosen_parent_indices[i]] = son
            self.chromosomes[chosen_parent_indices[i+1]] = daughter

    def mutate_add_gene(self, chromo_index):
        position = np.random.randint(0, len(self.chromosomes[chromo_index]) - 1) 
        new_gene = [np.random.randint(SCREEN_WIDTH), np.random.randint(SCREEN_HEIGHT)]
        self.chromosomes[chromo_index].insert(position, new_gene)

    def mutate_remove_gene(self, chromo_index):
        position = np.random.randint(1, len(self.chromosomes[chromo_index]) - 1) 
        del self.chromosomes[chromo_index][position]

    def mutate_edit_gene(self, chromo_index):
        position = np.random.randint(1, len(self.chromosomes[chromo_index]) - 1) 
        self.chromosomes[chromo_index][position] = [
                np.random.randint(SCREEN_WIDTH),
                np.random.randint(SCREEN_HEIGHT)
                ]

    def mutate(self):
        print("Performing Mutation")

        mutate_chosen = np.random.choice([True, False], size = POPULATION, p=[MUTATION_RATIO, 1-MUTATION_RATIO])
        for chromo_index in range(POPULATION):
            if not mutate_chosen[chromo_index]:
                continue
            mutate_type = np.random.randint(3)
            if mutate_type == 0:
                self.mutate_edit_gene(chromo_index)
            elif mutate_type == 1:
                self.mutate_add_gene(chromo_index)
            else:
                self.mutate_remove_gene(chromo_index)

    def validate(self, map): 
        print("Validating Population")
        i = 0
        while(i < len(self.chromosomes)):
            bezier = chromosome_to_bezier((self.chromosomes[i]))
            valid = True
            for obs in map.obstacles:
                _, proj_length = bezier.get_projection_of(obs.position)
                if(proj_length <= obs.radius):
                    valid = False
                    break
            if valid:
                i = i + 1
            else:
                del self.chromosomes[i]
        return
    def save_best_chromosome(self, filename, generation):
        # Find the index of the best chromosome based on fitness scores
        best_chromosome_index = np.argmin(self.fitness_scores)  # Minimize fitness score
        best_chromosome = self.chromosomes[best_chromosome_index]
    
        # Save the best chromosome to a file with the generation number
        with open(filename, 'a') as f:
            f.write(f"Generation {generation}: ")
            f.write(' '.join(map(str, [item for gene in best_chromosome for item in gene])) + '\n')
    def load_best_chromosomes(self, filename):
        best_chromosomes = []
    
        # Read the best chromosomes from the file
        with open(filename, 'r') as f:
            lines = f.readlines()
        
            # Parse each line and extract the chromosomes
            for line in lines:
                if line.strip():  # Skip empty lines
                    parts = line.strip().split(': ')
                    chromosome_data = list(map(int, parts[1].split()))
                    # Reconstruct the chromosome (assuming gene pairs)
                    chromosome = [chromosome_data[i:i + 2] for i in range(0, len(chromosome_data), 2)]
                    best_chromosomes.append(chromosome)
    
        return best_chromosomes
