"use client";

import { useState } from "react";
import { Stepper, Button, Group, Box} from "@mantine/core";
import { useForm } from "@mantine/form";
import { FormValues } from "@/src/types/mapping-form";
import { FullProfileResponse } from "@/src/types/mappings";
import {ProfileStep} from "./steps/ProfileStep";
import {SheetsStep} from "./steps/SheetsStep";
import {ColumnsStep} from "./steps/ColumnsStep";
import {RelationsStep} from "./steps/RelationsStep";
import {ReviewStep} from "./steps/ReviewStep";
import { mappingService } from "@/src/api/mappingService";
import { notifications } from "@mantine/notifications";
import { IconCheck, IconCircleXFilled } from "@tabler/icons-react";

type Props = {
  profile: FullProfileResponse | null | undefined;
  onClose: () => void;
};

export function MappingWizard({ profile, onClose }: Props) {
  const [active, setActive] = useState(0);
  const [mappingError, setError] = useState("");
  const [stepValid,setStepValid] = useState(true);

  const form = useForm<FormValues>({
    initialValues: {
      name: profile?.name ?? "",
      description: profile?.description ?? "",
      is_global: profile?.is_global ?? true,
      file_type: profile?.file_type ?? "", //Added hvb @ 03/12/2025
      sheets: profile?.sheets ?? [],
      column_mappings: profile?.column_mappings ?? [],
      relations: profile?.relations ?? []
    }
  });

  //const next = () => setActive((p) => Math.min(p + 1, 4));
  const next = () => setActive((p) => {
    if(stepValid){
      return Math.min(p + 1, 4)
    }
    else{
      notifications.show({
        title: 'Validation error',
        message: 'Clear validations on current page',
        color: 'red',
        icon: <IconCircleXFilled size="1.1rem" />,
      });
      return p;
    }
  });
  const prev = () => setActive((p) => Math.max(p - 1, 0));

  const jumpToPreview = ()=> setActive(4);
  const setStepValidity = (valid:boolean)=>{
    setStepValid(valid);
  }

  async function handleSubmit() {
    
    setError("");
    
    const cleaned = {
        ...form.values,
        sheets: form.values.sheets.map((s) => ({
          ...s,
          extra: s.extra && s.extra.length ? s.extra : null,
          cleanup: s.cleanup && s.cleanup.length ? s.cleanup : null
        }))
      };

    let done:boolean = false;
    let isCreate:boolean = false;
    
    try{
    if (profile) {
     let u = await mappingService.update(profile.id, cleaned);
     done = u != undefined && u != null;
    }
    else {
      isCreate = true;
      let d = await mappingService.create(cleaned as any);
      done = d != undefined && d != null;
    }
    
    if(done){
    notifications.show({
        title: (isCreate ? 'Create' : 'Update') + ' Success',
        message: 'Your mapping has been saved successfully',
        color: 'green',
        icon: <IconCheck size="1.1rem" />,
      });
      onClose();
    }
    else{
      notifications.show({
        title: (isCreate ? 'Create' : 'Update') + ' Failed',
        message: 'Failed to save mapping',
        color: 'red',
        icon: <IconCircleXFilled size="1.1rem" />,
      });
    }
    //In case you want to close even on error!
    //onClose();
  }
  catch(err:any){
    let errorMsg = (err.message || 'Failed to create mapping');
    if(err.status){
      if(err.status == 422){
          if(err.response.data.detail && err.response.data.detail.length > 0){
            errorMsg = err.response.data.detail[0].msg + err.response.data.detail[0].loc;
          }
      }else if(err.status == 400){
        //bad-request
        if(err.response.data.detail){
          errorMsg = err.response.data.detail;
        }
      }
    }
    
    notifications.show({
        title: (isCreate ? 'Create' : 'Update') + ' Failed',
        message: 'Failed to save mapping : ' + errorMsg,
        color: 'red',
        icon: <IconCircleXFilled size="1.1rem" />,
      });
    setError(errorMsg);
  }
  }

  return (
    <Box>
      <Stepper active={active} mt="xs" mb="lg">
        <Stepper.Step label="Profile" />
        <Stepper.Step label="Sheets" />
        <Stepper.Step label="Column Mapping" />
        <Stepper.Step label="Relations" />
        <Stepper.Step label="Review" />
      </Stepper>

      {active === 0 && <ProfileStep form={form} OnJsonFileLoad={jumpToPreview} />}
      {active === 1 && <SheetsStep form={form} setStepValid={setStepValidity} />}
      {active === 2 && <ColumnsStep form={form} />}
      {active === 3 && <RelationsStep form={form} />}
      {active === 4 && <ReviewStep form={form} errorMessage={mappingError} />}

      <Group justify="space-between" mt="xl">
        <Button variant="default" onClick={prev} disabled={active === 0}>
          Previous
        </Button>

        {active < 4 ? (
          <Button onClick={next}>Next</Button>
        ) : (
          <Button onClick={handleSubmit}>Save</Button>
        )}
      </Group>
    </Box>
  );
}
