import { type ReactNode, createContext, useContext, useMemo, useState } from "react";

interface FishfinderState {
  selectedFish: string | null;
  activeFilter: string[] | null;
  lastSql: string | null;
}

interface FishfinderActions {
  selectFish: (signal: string | null) => void;
  setFilter: (signals: string[] | null, sql: string | null) => void;
}

type FishfinderStore = FishfinderState & FishfinderActions;

const FishfinderContext = createContext<FishfinderStore | null>(null);

export function FishfinderProvider({ children }: { children: ReactNode }) {
  const [selectedFish, setSelectedFish] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<string[] | null>(null);
  const [lastSql, setLastSql] = useState<string | null>(null);

  const value = useMemo<FishfinderStore>(
    () => ({
      selectedFish,
      activeFilter,
      lastSql,
      selectFish: setSelectedFish,
      setFilter: (signals, sql) => {
        setActiveFilter(signals);
        setLastSql(sql);
      },
    }),
    [selectedFish, activeFilter, lastSql],
  );

  return <FishfinderContext.Provider value={value}>{children}</FishfinderContext.Provider>;
}

export function useFishfinderStore(): FishfinderStore {
  const ctx = useContext(FishfinderContext);
  if (!ctx) throw new Error("useFishfinderStore must be used within FishfinderProvider");
  return ctx;
}
