<template>
  <div class="blog-box blog-details">
    <div class="card">
      <img class="img-fluid w-100" :src="getImages('faq/learning-1.jpg')" alt="blog-main" />
      <div class="card-body">
        <div class="blog-details">
          <ul class="blog-social">
            <li class="digits">25 July 2023</li>
            <li><i class="icofont icofont-user"></i>Mark <span>Jecno </span></li>
            <li class="digits"><i class="icofont icofont-thumbs-up"></i>02<span>Hits</span></li>
            <li class="digits"><i class="icofont icofont-ui-chat"></i>598 Comments</li>
          </ul>
          <h4>Knowledge can be defined as awareness of facts or as practical skills. there is wide agreement among philosophers that it is a form of true belief.</h4>
          <div class="single-blog-content-top">
            <p>
              Knowledge can be defined as awareness of facts or as practical skills, and may also refer to familiarity with objects or situations. Knowledge of facts, also called propositional
              knowledge, is often defined as true belief that is distinct from opinion or guesswork by virtue of justification. While there is wide agreement among philosophers that it is a form of
              true belief, many controversies in philosophy focus on justification: whether it is needed at all, how to understand it, and whether something else besides it is needed.
            </p>
            <p>
              Knowledge can be produced in many different ways. The most important source is perception, which refers to the usage of the five senses. Many theorists also include introspection as a
              source of knowledge, not of external physical objects, but of one's own mental states. Other sources often discussed include memory, rational intuition, inference, and testimony.
              According to foundationalism, some of these sources are basic in the sense that they can justify beliefs without depending on other mental states. This claim is rejected by coherentists.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
</script>
