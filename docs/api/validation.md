# Validation API

Design-time analysis tools for FSM quality. These add **zero runtime
overhead** to FSMs that don't use them.

## Validators

```{eval-rst}
.. autoclass:: fast_fsm.FSMValidator
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.EnhancedFSMValidator
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fast_fsm.ValidationIssue
   :members:
   :undoc-members:
```

## Convenience Functions

```{eval-rst}
.. autofunction:: fast_fsm.validate_fsm

.. autofunction:: fast_fsm.quick_validation_report

.. autofunction:: fast_fsm.enhanced_validate_fsm

.. autofunction:: fast_fsm.quick_health_check

.. autofunction:: fast_fsm.validate_and_score

.. autofunction:: fast_fsm.compare_fsms

.. autofunction:: fast_fsm.batch_validate

.. autofunction:: fast_fsm.fsm_lint
```
