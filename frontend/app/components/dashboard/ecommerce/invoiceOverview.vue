<template>
  <div class="col-xl-6 box-col-12 des-xl-100 invoice-sec">
    <div class="card">
      <div class="card-header">
        <div class="header-top d-sm-flex justify-content-between align-items-center">
          <h5>Invoice Overview</h5>
          <div class="center-content">
            <p class="d-sm-flex align-items-center"><span class="m-r-10">$5,56548k</span><i class="toprightarrow-primary fa fa-arrow-up m-r-10 d-grid"></i>94% More Than Last Year</p>
          </div>
          <div class="setting-list"></div>
        </div>
      </div>
      <div class="card-body p-0">
        <div id="timeline-chart">
          <ChartInvoiceChart />
        </div>
      </div>
    </div>
  </div>
</template>
