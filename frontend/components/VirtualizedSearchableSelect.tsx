import { useState, useMemo, CSSProperties } from "react";
import {
  Combobox,
  InputBase,
  useCombobox,
} from "@mantine/core";
import { Virtuoso } from "react-virtuoso";

interface VirtualSearchSelectProps {
  data: string[];
  value: string | null;
  onChange: (value: string | null) => void;
  style?: CSSProperties;
}

export function VirtualizedSearchableSelect({
  data,
  value,
  onChange,
  style
}: VirtualSearchSelectProps) {
  const [search, setSearch] = useState("");

  const combobox = useCombobox({
    onDropdownClose: () => {
      combobox.resetSelectedOption();
      setSearch(""); // reset search box when closed
    },
  });

  const filtered = useMemo(() => {
    if (!search) return data;

    return data.filter((item) =>
      item.toLowerCase().includes(search.toLowerCase())
    );
  }, [search, data]);

  return (
    <Combobox
      store={combobox}
      onOptionSubmit={(val) => {
        onChange(val);     // <-- controlled value change
        combobox.closeDropdown();
      }}
    >
      {/* Selected value display (like Select) */}
      <Combobox.Target>
        <InputBase
          placeholder="Select value"
          value={value || ""}
          readOnly
          rightSection={<Combobox.Chevron />}
          onClick={() => combobox.toggleDropdown()}
          style={style}
        />
      </Combobox.Target>

      {/* Dropdown */}
      <Combobox.Dropdown>
        {/* Search input */}
        <Combobox.Search
          value={search}
          onChange={(e) => setSearch(e.currentTarget.value)}
          placeholder="Search..."
        />

        <Combobox.Options>
          <Virtuoso
            style={{ height: 200 }}
            totalCount={filtered.length}
            itemContent={(index) => {
              const item = filtered[index];
              return (
                <Combobox.Option key={item} value={item}>
                  {item}
                </Combobox.Option>
              );
            }}
          />
        </Combobox.Options>
      </Combobox.Dropdown>
    </Combobox>
  );
}
