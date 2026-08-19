<template>
  <div class="sidebar-user text-center">
    <a class="setting-primary" href="javascript:void(0)">
      <Icon name="material-symbols:settings-outline-rounded" class="" size="20" />
    </a>

    <img class="img-90 rounded-circle" src="/images/dashboard/1.png" alt="" />
    <div class="badge-bottom"><span class="badge badge-primary">New</span></div>

    <nuxt-link to="/users/profile">
      <h6 class="mt-3 f-14 f-w-600">Emay Walter</h6>
    </nuxt-link>
    <p class="mb-0 font-roboto">Human Resources Department</p>
    <ul>
      <li>
        <span
          ><span class="counter"> <CommenNumberAnimation data="19.8" /> </span>k</span
        >
        <p>Follow</p>
      </li>
      <li>
        <span class="count">2 year</span>
        <p>Experince</p>
      </li>
      <li>
        <span
          ><span class="counter"> <CommenNumberAnimation data="95.2" /> </span>k</span
        >
        <p>Follower</p>
      </li>
    </ul>
  </div>
</template>
