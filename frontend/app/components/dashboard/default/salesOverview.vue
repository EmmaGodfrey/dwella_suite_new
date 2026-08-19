<template>
  <div class="col-xl-7 box-col-12 des-xl-100 dashboard-sec">
    <div class="card income-card">
      <div class="card-header">
        <div class="header-top d-sm-flex align-items-center">
          <h5>Sales overview</h5>
          <div class="center-content">
            <p class="d-sm-flex align-items-center">
              <span class="font-primary m-r-10 f-w-700">$859.25k</span><i class="toprightarrow-primary fa fa-arrow-up m-r-10 d-grid"></i>86% More than last year
            </p>
          </div>
          <div class="setting-list"></div>
        </div>
      </div>
      <div class="card-body p-0">
        <div id="chart-timeline-dashbord">
          <ChartSalesChart />
        </div>
      </div>
    </div>
  </div>
</template>
