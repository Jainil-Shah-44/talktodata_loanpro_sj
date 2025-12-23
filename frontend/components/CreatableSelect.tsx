"use client";

import { useEffect, useState } from "react";
import { Combobox, Group, InputBase, useCombobox } from "@mantine/core";
import { IconCirclePlusFilled, IconEdit } from "@tabler/icons-react";

type MantineFormInputProps = {
  value?: string;
  onChange: (event: any) => void;
  onBlur?: () => void;
  error?: string;
};

interface CreatableSelectProps {
  label: string;
  data: string[];
  // ---- OPTION 1 (Mantine form) ----
  formProps?: MantineFormInputProps; // 👈 accept Mantine form props directly
  
  // ---- OPTION 2 (standalone state) ----
  value?: string;
  onChange?: (value: string) => void;

  required?: boolean;
  isAddOption?:boolean
}

export function CreatableSelect({
  label,
  data,
  formProps,
  required,

  value: outsideValue,
  onChange: outsideOnChange,

  isAddOption

}: CreatableSelectProps) {
  // const [options, setOptions] = useState(data);
  const [options, setOptions] = useState<string[]>([]);
  const combobox = useCombobox();

  if(isAddOption == undefined)
    isAddOption = true;

  useEffect(() => {
    setOptions(data);   // ⬅ make sure dropdown updates when data loads
  }, [data]);

  // use formProps if provided, else fallback to plain value/onChange
  const value = formProps?.value ?? outsideValue ?? "";

  const handleChange = (val: string) => {
    if (formProps) formProps.onChange(val);
    else outsideOnChange?.(val);
  };

  const handleSubmit = (option: string) => {
    if (!options.includes(option)) {
      setOptions((prev) => [...prev, option]);
    }
    handleChange(option);
    combobox.closeDropdown();
  }

  return (
    <Combobox store={combobox} onOptionSubmit={handleSubmit}>
      <Combobox.Target>
        <InputBase
          label={label}
          required={required}
          value={value}
          onChange={(event) => {
            handleChange(event.currentTarget.value);
            combobox.openDropdown();
            combobox.updateSelectedOptionIndex();
          }}
          placeholder="Select or type to create…"
        />
      </Combobox.Target>

      <Combobox.Dropdown>
        <Combobox.Options>
          {options.map((item) => (
            <Combobox.Option value={item} key={item}>
              {item}
            </Combobox.Option>
          ))}

          {value.trim() && !options.includes(value) && (
            <Combobox.Option value={value}>
              {isAddOption ? (
                <><IconCirclePlusFilled /> Create "{value}"</>
              ) : (
                <><Group><IconEdit /> "{value}"</Group></>
              )}
            </Combobox.Option>
          )}
        </Combobox.Options>
      </Combobox.Dropdown>
    </Combobox>
  );
}
