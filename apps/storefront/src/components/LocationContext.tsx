"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { ApiError, getCities, type CityOption } from "@/lib/api";

const STORAGE_KEY = "dk_selected_city_code";

interface LocationContextType {
  selectedCity: CityOption | null;
  cities: CityOption[];
  setSelectedCity: (city: CityOption | null) => void;
  isLoading: boolean;
}

const LocationContext = createContext<LocationContextType | null>(null);

export function LocationProvider({ children }: { children: ReactNode }) {
  const [selectedCity, setSelectedCityState] = useState<CityOption | null>(null);
  const [cities, setCities] = useState<CityOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getCities()
      .then((list) => {
        setCities(list);
        if (list.length === 0) return;

        const saved = localStorage.getItem(STORAGE_KEY);
        const match = saved ? list.find((c) => c.code === saved) : null;
        if (match) {
          setSelectedCityState(match);
        } else {
          const hcm = list.find((c) => c.code === "HCM");
          setSelectedCityState(hcm ?? list[0]);
        }
      })
      .catch(() => {
        // Cities unavailable — degrade gracefully
      })
      .finally(() => setIsLoading(false));
  }, []);

  const setSelectedCity = useCallback((city: CityOption | null) => {
    setSelectedCityState(city);
    if (city) {
      localStorage.setItem(STORAGE_KEY, city.code);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const value = useMemo<LocationContextType>(
    () => ({ selectedCity, cities, setSelectedCity, isLoading }),
    [selectedCity, cities, setSelectedCity, isLoading]
  );

  return <LocationContext.Provider value={value}>{children}</LocationContext.Provider>;
}

export function useLocation(): LocationContextType {
  const ctx = useContext(LocationContext);
  if (!ctx) {
    throw new Error("useLocation must be used within LocationProvider");
  }
  return ctx;
}
