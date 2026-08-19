<template>
  <div class="row">
    <div class="col-sm-4">
      <div class="mb-3">
        <label>Project Rate</label>
        <input class="form-control" type="text" placeholder="Enter project Rate" />
      </div>
    </div>
    <div class="col-sm-4">
      <div class="mb-3">
        <label>Project Type</label>
        <select class="form-select">
          <option>Hourly</option>
          <option>Fix price</option>
        </select>
      </div>
    </div>
    <div class="col-sm-4">
      <div class="mb-3">
        <label>Priority</label>
        <select class="form-select">
          <option>Low</option>
          <option>Medium</option>
          <option>High</option>
          <option>Urgent</option>
        </select>
      </div>
    </div>
  </div>
  <div class="row">
    <div class="col-sm-4">
      <div class="mb-3">
        <label>Project Size</label>
        <select class="form-select">
          <option>Small</option>
          <option>Medium</option>
          <option>Big</option>
        </select>
      </div>
    </div>
    <div class="col-sm-4">
      <div class="mb-3">
        <label>Starting date</label>
        <input class="datepicker-here form-control" type="date" data-language="en" />
      </div>
    </div>
    <div class="col-sm-4">
      <div class="mb-3">
        <label>Ending date</label>
        <input class="datepicker-here form-control" type="date" data-language="en" />
      </div>
    </div>
  </div>
</template>
