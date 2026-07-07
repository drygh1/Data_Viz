import { FishTimelineMap } from "./panes/FishTimelineMap";
import { OverviewMap } from "./panes/OverviewMap";
import { QueryBar } from "./panes/QueryBar";
import { FishfinderProvider } from "./state/store";

export function App() {
  return (
    <FishfinderProvider>
      <div className="app-layout">
        <div className="app-top">
          <OverviewMap />
          <FishTimelineMap />
        </div>
        <QueryBar />
      </div>
    </FishfinderProvider>
  );
}
