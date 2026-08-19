import React, { Fragment, useState, useContext } from "react";
import { LI } from "../../../AbstractElements";
import ConfigDB from "../../../Config/ThemeConfig";
import CustomizerContext from "../../../_helper/Customizer";

const MoonLight = () => {
  const { addMixBackgroundLayout } = useContext(CustomizerContext);
  const [moonlight, setMoonlight] = useState(false);
  const localStorageLayout = localStorage.getItem("layout_type") || ConfigDB.settings.layout_type;

  const MoonlightToggle = (light) => {
    if (light) {
      addMixBackgroundLayout("light-only");
      document.body.classList.add("light-only");
      document.body.classList.remove("dark-only");
      document.body.classList.remove("dark-sidebar");
      document.body.classList.add(localStorageLayout);
      setMoonlight(!light);
    } else {
      addMixBackgroundLayout("dark-only");
      document.body.classList.add("dark-only");
      document.body.classList.remove("dark-sidebar");
      document.body.classList.remove("light-only");
      document.body.classList.add(localStorageLayout);
      setMoonlight(!light);
    }
  };
  return (
    <Fragment>
      <LI>
        <div className="mode" onClick={() => MoonlightToggle(moonlight)}>
          {moonlight ? <i className="fa fa-lightbulb-o"></i> : <i className="fa fa-moon-o"></i>}
        </div>
      </LI>
    </Fragment>
  );
};

export default MoonLight;
