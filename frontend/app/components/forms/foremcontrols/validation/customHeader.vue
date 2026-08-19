<template>
  <div class="card-header pb-0">
    <h5>Custom styles</h5>
    <span class="mt-2"
      >For custom Bootstrap form validation messages, you’ll need to add the <code class="text-danger">novalidate</code> boolean attribute to your <code class="text-danger">&lt;form&gt;</code>. This
      disables the browser default feedback tooltips, but still provides access to the form validation APIs in JavaScript. Try to submit the form below; our JavaScript will intercept the submit button
      and relay feedback to you.</span
    ><span>When attempting to submit, you’ll see the <code class="text-danger">:invalid </code> and <code class="text-danger">:valid </code> styles applied to your form controls.</span>
  </div>
</template>
