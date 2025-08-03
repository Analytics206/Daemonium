'use client';

import React, { useState } from 'react';
import { Button, type ButtonProps } from '@/components/ui/button';
import { Filter, X } from 'lucide-react';

const periods = [
  'Ancient (Before 500 CE)',
  'Medieval (500-1500 CE)',
  'Renaissance (1400-1600)',
  'Modern (1600-1800)',
  'Contemporary (1800+)',
];

const specialties = [
  'Ethics',
  'Metaphysics',
  'Epistemology',
  'Logic',
  'Political Philosophy',
  'Existentialism',
  'Stoicism',
  'Phenomenology',
];

export function PhilosopherFilters() {
  const [selectedPeriods, setSelectedPeriods] = useState<string[]>([]);
  const [selectedSpecialties, setSelectedSpecialties] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  const togglePeriod = (period: string) => {
    setSelectedPeriods(prev =>
      prev.includes(period)
        ? prev.filter(p => p !== period)
        : [...prev, period]
    );
  };

  const toggleSpecialty = (specialty: string) => {
    setSelectedSpecialties(prev =>
      prev.includes(specialty)
        ? prev.filter(s => s !== specialty)
        : [...prev, specialty]
    );
  };

  const clearFilters = () => {
    setSelectedPeriods([]);
    setSelectedSpecialties([]);
  };

  const hasActiveFilters = selectedPeriods.length > 0 || selectedSpecialties.length > 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2 flex items-center space-x-2"
        >
          <Filter className="w-4 h-4" />
          <span>Filters</span>
          {hasActiveFilters && (
            <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
              {selectedPeriods.length + selectedSpecialties.length}
            </span>
          )}
        </button>

        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-9 rounded-md px-3"
          >
            <X className="w-4 h-4 mr-1" />
            Clear all
          </button>
        )}
      </div>

      {showFilters && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-4 border rounded-lg bg-muted/50">
          <div>
            <h3 className="font-medium mb-3">Time Period</h3>
            <div className="space-y-2">
              {periods.map((period) => (
                <label key={period} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedPeriods.includes(period)}
                    onChange={() => togglePeriod(period)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">{period}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-medium mb-3">Specialty</h3>
            <div className="space-y-2">
              {specialties.map((specialty) => (
                <label key={specialty} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedSpecialties.includes(specialty)}
                    onChange={() => toggleSpecialty(specialty)}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">{specialty}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}

      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2">
          {selectedPeriods.map((period) => (
            <span
              key={period}
              className="inline-flex items-center px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
            >
              {period}
              <button
                onClick={() => togglePeriod(period)}
                className="ml-1 hover:text-blue-600"
                aria-label={`Remove ${period} filter`}
                title={`Remove ${period} filter`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
          {selectedSpecialties.map((specialty) => (
            <span
              key={specialty}
              className="inline-flex items-center px-3 py-1 text-xs bg-green-100 text-green-800 rounded-full"
            >
              {specialty}
              <button
                onClick={() => toggleSpecialty(specialty)}
                className="ml-1 hover:text-green-600"
                aria-label={`Remove ${specialty} filter`}
                title={`Remove ${specialty} filter`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
